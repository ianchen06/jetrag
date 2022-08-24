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

app = Flask(__name__, template_folder='./manager/templates')
app.logger.setLevel(logging.INFO)
cfg = get_config(os.getenv("JETRAG_ENV", "dev"))
db = Dynamodb("jetrag3")
notifier = SlackNotifier(cfg['notifications']['slack'])
valid_crawler_names = ['moosejaw']

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
    name = data['name']
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
    db.update(Key={"pk": f"DONE#{name}#{dt}"}, AttributeUpdates=attr_updates)
    notifier.send_info({'text': f"{name} start"})
    return jsonify({})

@app.route("/worker/done", methods=["POST"])
@auth_required
def worker_done():
    app.logger.info("worker_done")
    now = int(time.time())
    data = request.get_json()
    app.logger.info("got json")
    dt = data["dt"]
    name = data['name']
    app.logger.info("before load")
    
    loader_class = MoosejawLoader
    
    app.logger.info("after load, before db get")
    res = db.get(f"DONE#{name}#{dt}")
    item = res.get("Item")
    if item:
        start_dt = item.get("start_dt", 0)
        app.logger.info(f"start_dt is {start_dt}")
        end_dt = item.get("end_dt", 0)
        dt_diff = now - end_dt
        app.logger.info(dt_diff)
        if dt_diff > 600:
            try:
                db.update(Key={"pk": f"DONE#{name}#{dt}"},
                    UpdateExpression="set end_at = :r",
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
            app.logger.info(datetime.datetime.fromtimestamp(end_dt))
            loader = loader_class(cfg['db']['sqlalchemy'], '', dt, True)
            before_dt = datetime.datetime.fromtimestamp(start_dt).strftime('%Y-%m-%d 00:00:00')
            app.logger.info(f"cleanup before {before_dt}")
            print("before cleanup")
            loader.cleanup(before_dt)
            notifier.send_info({'text': f"{name} done"})

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
