import logging

import click

import crawlers
from worker import Worker
from db.redis import RedisStore
from db.dynamodb import DynamodbStore
from q.redis import RedisQueue
from q.sqs import SqsQueue

logging.basicConfig(level=logging.INFO)

cfg = {
    'test': {},
    'moosejaw': {
        'base_url': 'https://moosejaw.com',
        'headers': {
            'authority': 'www.moosejaw.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://www.moosejaw.com/navigation/footwear',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36',
        }
    }
}

DB = RedisStore()
QUEUE = RedisQueue

def get_crawler(name, cfg, queue, db):
    crawler_class = crawlers.get_crawler_class(name)
    crawler = crawler_class(cfg, queue, db)
    return crawler

@click.group()
def cli():
    pass

@click.command('crawl')
@click.argument('name')
def crawl(name):
    # TODO: add if name == 'all', dispatch all crawlers
    crawler_queue = QUEUE(name)
    crawler_cfg = cfg[name]
    crawler = get_crawler(name, crawler_cfg, crawler_queue, DB)
    crawler.dispatch()

@click.group()
def worker():
    pass

@click.command('start')
@click.argument('name')
def worker_start(name):
    # TODO: add if name == 'all', start workers for all crawlers
    click.echo(f'starting worker for {name}')
    crawler_queue = QUEUE(name)
    crawler_cfg = cfg[name]
    crawler = get_crawler(name, crawler_cfg, crawler_queue, DB)
    w = Worker(crawler)
    w.start()

@click.group()
def queue():
    pass

@click.command('create')
@click.argument('name')
def queue_create(name):
    queue_ctl = q.get_queue_ctl_klass(cfg['queue']['broker'])()
    res = queue_ctl.create_queue(name)
    click.echo(f"queue {res} created")

@click.command('list')
def queue_list():
    queue_ctl = q.get_queue_ctl_klass(cfg['queue']['broker'])()
    res = queue_ctl.list_queues()
    click.echo(res)

cli.add_command(worker)
cli.add_command(queue)
cli.add_command(crawl)
worker.add_command(worker_start)
queue.add_command(queue_create)
queue.add_command(queue_list)

def main():
    cli()

if __name__ == '__main__':
    # TODO: read config here and pass down data using Context
    main()