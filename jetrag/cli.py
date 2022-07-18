import logging
import os

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
        }
    },
    'test': {},
    'moosejaw': {
        'base_url': 'https://moosejaw.com',
        'headers': {
            'authority': 'www.moosejaw.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://www.moosejaw.com/',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }
    }
}

DB = S3Store
QUEUE = SqsQueue
QUEUE_CTL = Sqs
DRIVER = EcsDriver
NOTIFIER = SlackNotifier
METADB = DynamodbStore

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def get_crawler(name, cfg, queue, db, notifier, metadb):
    crawler_class = crawlers.get_crawler_class(name)
    crawler = crawler_class(cfg, queue, db, notifier, metadb)
    return crawler

@click.group()
def cli():
    pass

@click.group()
def crawler():
    pass

@click.command('dispatch')
@click.argument('name')
def crawler_dispatch(name):
    crawler_queue = QUEUE(name)
    crawler_cfg = cfg[name]
    crawler = get_crawler(name, crawler_cfg, crawler_queue, DB)
    crawler.dispatch()

@click.command('start')
@click.argument('name')
def crawler_start(name):
    # TODO: add if name == 'all', dispatch all crawlers
    worker_driver = DRIVER(cfg['driver']['ecs'], name)
    worker_driver.launch()

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
    db = DB(cfg['db']['s3']['bucket_name'], cfg['db']['s3']['base_path'])
    notifier = NOTIFIER(SLACK_WEBHOOK_URL)
    metadb = METADB()
    crawler = get_crawler(name, crawler_cfg, crawler_queue, db, notifier, metadb)
    w = Worker(cfg['worker'], crawler, worker_driver)
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

# crawler subcommands
crawler.add_command(crawler_dispatch)
crawler.add_command(crawler_start)

# worker subcommands
worker.add_command(worker_start)

# queue subcommands
queue.add_command(queue_create)
queue.add_command(queue_list)

def main():
    cli()

if __name__ == '__main__':
    # TODO: read config here and pass down data using Context
    main()