import logging
import os
import datetime

import click
import requests

import crawlers
from worker import Worker


logging.basicConfig(level=logging.INFO)

def get_crawler(name, cfg, queue, raw_store, conn_str, notifier):
    crawler_class = crawlers.get_crawler_class(name)
    crawler = crawler_class(cfg, queue, raw_store, conn_str, notifier)
    return crawler

def get_notifier(cfg):
    notifications_type = cfg['notifications']['type']
    if notifications_type == 'slack':
        from notification.slack import SlackNotifier as notifier
    return notifier(cfg['notifications'][notifications_type])

def get_html_store(cfg):
    html_store_type = cfg['html_store']['type']
    if html_store_type == 's3':
        from db.s3 import S3Store as html_store
    return html_store(cfg['html_store'][html_store_type])

def get_queue(cfg, name):
    supported_queue_types = ['sqs']
    queue_type = cfg['queue']['type']
    if queue_type not in supported_queue_types:
        raise(f"queue type {queue_type} is not supported")
    if queue_type == 'sqs':
        from q.sqs import SqsQueue as queue
    return queue(cfg['queue']['name_template'].format(name))

def get_cfg(env='dev'):
    if env == 'dev':
        from config.dev import cfg
    if env == 'prod':
        from config.prod import cfg
    return cfg

def get_driver(cfg, name):
    driver_type = cfg['driver']['type']
    envvars = ["JETRAG_ENV", "RDS_AWS_ACCESS_KEY_ID", "RDS_AWS_SECRET_ACCESS_KEY"]
    environment = []
    for envvar in envvars:
        environment.append({
            'name': envvar,
            'value': os.getenv(envvar)
        })
    if driver_type == 'ecs':
        from driver.ecs import EcsDriver as driver
    return driver(cfg['driver'][driver_type], name, environment)

@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['cfg'] = get_cfg(os.getenv("JETRAG_ENV", 'dev'))
    
@click.group()
def crawler():
    pass

@click.command('test')
@click.pass_context
@click.argument('name')
def crawler_test(ctx, name):
    click.echo(ctx.obj)

@click.command('dispatch')
@click.argument('name')
@click.pass_context
def crawler_dispatch(ctx, name):
    cfg = ctx.obj['cfg']
    _crawler_dispatch(cfg, name)

def _crawler_dispatch(cfg, name):
    crawler_queue = get_queue(cfg, name)
    crawler_cfg = cfg[name]
    notifier = get_notifier(crawler_cfg)
    crawler = get_crawler(name, crawler_cfg, crawler_queue, '', cfg['db']['sqlalchemy'], notifier)
    crawler.dispatch()

@click.command('start')
@click.argument('name')
@click.pass_context
def crawler_start(ctx, name):
    cfg = ctx.obj['cfg']
    dt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    requests.post(cfg['manager']['url']+'/worker/start',
                headers={'Authorization': f"Bearer {cfg['manager']['token']}"},
                json={'dt': dt, 'name': f"{name}-{cfg['env']}"})
    _crawler_dispatch(cfg, name)
    worker_driver = get_driver(cfg, name)
    for num in range(cfg[name]['concurrency']):
        worker_driver.launch(['python', 'jetrag/cli.py', 'worker', 'start', name])

@click.command('launch')
@click.argument('name')
@click.pass_context
def crawler_launch(ctx, name):
    cfg = ctx.obj['cfg']
    worker_driver = get_driver(cfg, name)
    worker_driver.launch(['python', 'jetrag/cli.py', 'worker', 'start', name])

@click.group()
def worker():
    pass

@click.command('start')
@click.argument('name')
@click.pass_context
def worker_start(ctx, name):
    click.echo(f'starting worker for {name}')
    cfg = ctx.obj['cfg']
    worker_driver = get_driver(cfg, name)
    crawler_queue = get_queue(cfg, name)
    crawler_cfg = cfg[name]
    html_store = get_html_store(cfg)
    notifier = get_notifier(crawler_cfg)
    crawler = get_crawler(name, crawler_cfg, crawler_queue, html_store, cfg['db']['sqlalchemy'], notifier)
    w = Worker(cfg, crawler, worker_driver, notifier)
    w.start()

@click.command('execute')
@click.argument('name')
@click.argument('method')
@click.argument('args')
@click.pass_context
def crawler_execute(ctx, name, method, args):
    crawler = get_debug_crawler(name)
    func = getattr(crawler, method)
    res = func(args)
    return res

def get_debug_crawler(name):
    cfg = get_cfg(os.getenv("JETRAG_ENV", 'dev'))
    worker_driver = get_driver(cfg, name)
    crawler_queue = get_queue(cfg, name)
    crawler_cfg = cfg[name]
    html_store = get_html_store(cfg)
    notifier = get_notifier(crawler_cfg)
    crawler = get_crawler(name, crawler_cfg, crawler_queue, html_store, cfg['db']['sqlalchemy'], notifier)
    return crawler

# cli subcommands
cli.add_command(worker)
cli.add_command(crawler)

# crawler subcommands
crawler.add_command(crawler_dispatch)
crawler.add_command(crawler_start)
crawler.add_command(crawler_launch)
crawler.add_command(crawler_test)
crawler.add_command(crawler_execute)

# worker subcommands
worker.add_command(worker_start)

# queue subcommands

def main():
    cli()

if __name__ == '__main__':
    # TODO: read config here and pass down data using Context
    main()