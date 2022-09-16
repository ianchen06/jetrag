from functools import wraps
import datetime
import time
import os
import logging

from flask import Flask, jsonify, request, make_response, render_template
from yaml import load
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from db.dynamodb import Dynamodb
from notification.slack import SlackNotifier
from config import get_config
from loaders.moosejaw import MoosejawLoader
from loaders.zappos import ZapposLoader

app = Flask(__name__, template_folder='./manager/templates')
app.logger.setLevel(logging.INFO)
cfg = get_config(os.getenv("JETRAG_ENV", "dev"))
db = Dynamodb("jetrag3")

def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            return make_response(jsonify({"error": "unauthorized"}), 401)
        return f(*args, **kwargs)

    return wrapper

@app.route("/worker/start", methods=["POST"])
@auth_required
def worker_start():
    now = int(time.time())
    data = request.get_json()
    dt = data["dt"]
    name_env = data['name']
    name = name_env.split("-")[0]
    attr_updates = {
        'start_dt': {
            'Value': now,
            'Action': 'PUT'
        },
        'end_dt': {
            'Value': 0,
            'Action': 'PUT'
        }
    }
    db.update(Key={"pk": f"DONE#{name_env}#{dt}"}, AttributeUpdates=attr_updates)
    crawler_cfg = cfg[name]
    notifier = SlackNotifier(crawler_cfg['notifications']['slack'])
    notifier.send_info({'text': f"{name_env} start"})
    return jsonify({})

@app.route("/worker/done", methods=["POST"])
@auth_required
def worker_done():
    now = int(time.time())
    data = request.get_json()
    dt = data["dt"]
    name_env = data['name']
    name = name_env.split("-")[0]

    loader_class_map = {
        'moosejaw': MoosejawLoader,
        'zappos': ZapposLoader,
    }
    
    loader_class = loader_class_map.get(name, "")
    if not loader_class:
        raise Exception(f"loader_class not found for name {name}")
    
    res = db.get(f"DONE#{name_env}#{dt}")
    item = res.get("Item")
    if item:
        start_dt = item.get("start_dt", 0)
        end_dt = item.get("end_dt", 0)
        dt_diff = now - end_dt
        if dt_diff > 600:
            try:
                db.update(Key={"pk": f"DONE#{name_env}#{dt}"},
                    UpdateExpression="set end_dt = :r",
                    ExpressionAttributeValues={
                        ':r': now
                    },
                    ConditionExpression=Attr("end_dt").eq(0))
            except ClientError as err:
                if err.response["Error"]["Code"] == 'ConditionalCheckFailedException':
                    # Somebody changed the item in the db while we were changing it!
                    raise ValueError("end_dt updated since read, retry!") from err
                else:
                    raise err
            loader = loader_class(cfg['db']['sqlalchemy'], '', dt, True)
            before_dt = datetime.datetime.fromtimestamp(start_dt).strftime('%Y-%m-%d 00:00:00')
            loader.cleanup(before_dt)
            crawler_cfg = cfg[name]
            notifier = SlackNotifier(crawler_cfg['notifications']['slack'])
            notifier.send_info({'text': f"{name_env} done"})

    return jsonify(item)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        return render_template("index.html")

@app.route("/")
def home():
    app.logger.info("home")
    return render_template('index.html')
