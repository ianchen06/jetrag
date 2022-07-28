import logging
import os
import datetime

import click

import crawlers
from worker import Worker
from db.redis import RedisStore
from db.s3 import S3Store
from q.redis import RedisQueue
from q.sqs import Sqs, SqsQueue
from driver.ecs import EcsDriver
from db.dynamodb import DynamodbStore
from notification.slack import SlackNotifier

logging.basicConfig(level=logging.INFO)

cfg = {
    'env': 'dev',
    'queue_name_prefix': 'jetrag3-sqs-',
    'worker': {},
    'driver': {
        'ecs': {
            'cluster_name': 'jetrag3-cluster',
            'container_name': 'jetrag3',
            'count': 1,
            'task_definition': 'jetrag3-crawler',
            'task_role_arn': 'arn:aws:iam::068993006585:role/jetrag3-crawler-ecs-task-role',
            'subnet_id': 'subnet-0d8af4bf75baa139e',
            'security_group': 'sg-0f326cd91a4b8cfbf'
        }
    },
    'db': {
        's3': {
            'bucket_name': 'jetrag3',
            'base_path': ''
        },
        'sqlalchemy': {
            #'conn_str': 'mysql+pymysql://root:mysql@localhost:3306',
            'conn_str': 'mysql+auroradataapi://:@',
            'aws_access_key_id': os.getenv("RDS_AWS_ACCESS_KEY_ID"),
            'aws_secret_access_key': os.getenv("RDS_AWS_SECRET_ACCESS_KEY"),
            'connect_args': {
                'aurora_cluster_arn': 'arn:aws:rds:ap-northeast-1:179980757190:cluster:jetrag-en-db',
                'secret_arn': 'arn:aws:secretsmanager:ap-northeast-1:179980757190:secret:rds-db-credentials/cluster-LCOGPYN4KMRUKNKL24EDFTGZKE/jetrag-j0paFO',
            }
        }
    },
    'test': {},
    'moosejaw': {
        'concurrency': 5,
        'base_url': 'https://moosejaw.com',
        'headers': {
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Host': 'www.moosejaw.com',
                'TE': 'Trailers',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:88.0) Gecko/20100101 Firefox/88.0',
        },
    }
}

RAW_STORE = S3Store
QUEUE = SqsQueue
QUEUE_CTL = Sqs
DRIVER = EcsDriver
NOTIFIER = SlackNotifier
METADB = DynamodbStore

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def get_crawler(name, cfg, queue, raw_store, conn_str, notifier, metadb):
    crawler_class = crawlers.get_crawler_class(name)
    crawler = crawler_class(cfg, queue, raw_store, conn_str, notifier, metadb)
    return crawler

@click.group()
def cli():
    pass

@click.group()
def loader():
    pass

@click.command('start')
@click.argument('name')
def loader_start(name):
    dt = datetime.datetime.now().strftime('%Y%m%d')
    cfg['driver']['ecs']['task_definition'] = cfg['driver']['ecs']['task_definition']+'-etl'
    loader_driver = DRIVER(cfg['driver']['ecs'], name)
    loader_driver.launch(['python', 'jetrag/load.py', dt])
    
@click.group()
def crawler():
    pass

@click.command('dispatch')
@click.argument('name')
def crawler_dispatch(name):
    _crawler_dispatch(name)

def _crawler_dispatch(name):
    crawler_queue = QUEUE(cfg['queue_name_prefix'] + name + '-' + cfg['env'])
    crawler_cfg = cfg[name]
    notifier = NOTIFIER(SLACK_WEBHOOK_URL)
    metadb = METADB()
    crawler = get_crawler(name, crawler_cfg, crawler_queue, '', cfg['db']['sqlalchemy'], notifier, metadb)
    crawler.dispatch()

@click.command('start')
@click.argument('name')
def crawler_start(name):
    # TODO: add if name == 'all', dispatch all crawlers
    _crawler_dispatch(name)
    worker_driver = DRIVER(cfg['driver']['ecs'], name)
    for num in range(cfg['moosejaw']['concurrency']):
        worker_driver.launch(['python', 'jetrag/cli.py', 'worker', 'start', name])

@click.group()
def worker():
    pass

@click.command('start')
@click.argument('name')
def worker_start(name):
    # TODO: add if name == 'all', start workers for all crawlers
    click.echo(f'starting worker for {name}')
    worker_driver = DRIVER(cfg['driver']['ecs'], name)
    crawler_queue = QUEUE(cfg['queue_name_prefix'] + name + '-' + cfg['env'])
    crawler_cfg = cfg[name]
    raw_store = RAW_STORE(cfg['db']['s3']['bucket_name'], cfg['db']['s3']['base_path'])
    notifier = NOTIFIER(SLACK_WEBHOOK_URL)
    metadb = METADB()
    crawler = get_crawler(name, crawler_cfg, crawler_queue, raw_store, cfg['db']['sqlalchemy'], notifier, metadb)
    w = Worker(cfg['worker'], crawler, worker_driver, notifier,metadb)
    w.start()

@click.group()
def queue():
    pass

@click.command('create')
@click.argument('name')
def queue_create(name):
    res = QUEUE_CTL.create_queue(name)
    click.echo(f"queue {res} created")

@click.command('list')
def queue_list():
    res = QUEUE_CTL.list_queues()
    click.echo(res)

@click.command('put')
@click.argument('name')
@click.argument('msg')
def queue_put(name, msg):
    c = QUEUE(name)
    c.put(msg)

# cli subcommands
cli.add_command(worker)
cli.add_command(queue)
cli.add_command(crawler)
cli.add_command(loader)

# crawler subcommands
crawler.add_command(crawler_dispatch)
crawler.add_command(crawler_start)

# worker subcommands
worker.add_command(worker_start)

# queue subcommands
queue.add_command(queue_create)
queue.add_command(queue_list)

# loader subcommands
loader.add_command(loader_start)

def main():
    cli()

if __name__ == '__main__':
    # TODO: read config here and pass down data using Context
    main()