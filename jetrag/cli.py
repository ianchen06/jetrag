import logging

import click

import crawlers
from worker import Worker
from db.redis import RedisStore
from db.s3 import S3Store
from q.redis import RedisQueue
from q.sqs import Sqs, SqsQueue
from driver.ecs import EcsDriver

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
            # Requests sorts cookies= alphabetically
            'cookie': '_pxhd=FKuxWcVsECQLQDaUyGHqukKwLB0O3K4YCce-yaokAezK4ZkybWnASIzDfLCifDV/5mT4KWuJFkQDLHyBzTCwzA==:uBiU/p5tNVMB9uyP35ZWuqfMLmG69MfsVzBZqx8IZZtsBVp/vWvUqvY/ivihvXwdINjIUVz7Q6kqilnkczoDsRUx41hofwPCU7g7G8EzkB8=; mt.v=2.334327528.1656574747974; _ga=GA1.2.1452687466.1656574748; WC_DeleteCartCookie_10208=true; __attentive_id=82888f84f8c340a496c4d37d2cf364d8; __attentive_cco=1656574748482; cmTPSet=Y; CoreID6=29567222439516565747485&ci=90220406; tracker_device=ecaf859c-bfdf-45a8-a4a1-b3d5d34dc901; WC_SESSION_ESTABLISHED=true; WC_ACTIVEPOINTER=-1%2C10208; SOD=; _gcl_au=1.1.855829347.1656574749; _fbp=fb.1.1656574748868.1914563802; IR_gbd=moosejaw.com; rj2session=0090454b-1790-4e7f-900c-5681b95c1f5c; a1ashgd=4e8bb097d9a71baf0e415e181d552138; _pin_unauth=dWlkPU5EUTFPV0k0TlRZdFlUWmlNeTAwWmpJeExUaG1NREF0WlRVMVlURmpNR00yWVRSaA; pxcts=bce11c1c-f847-11ec-9c3f-63536e715558; _pxvid=b857b547-f847-11ec-b696-425258504e47; BVImplmain_site=18209; NoCookie=true; LPVID=U2MzZhODE3NjAzYjg0OWUw; priceMode=1; analyticsPreCategoryAttributes=""; CompareItems_10208=; promoCode=BREAKFAST|; WC_PERSISTENT=V3ze9sk%2F8LuYHGEfO8X6oVqsaO5PQ7mFAnVuAXjC%2Fzw%3D%3B2022-06-30+09%3A41%3A56.512_1656574746783-207015_10208_207354647%2C-1%2CUSD%2C2022-06-30+09%3A41%3A56.512_10208; searchTermHistory=%7Cjackets%7Cclothing%7Cmens%20goretex%20jackets; analyticsSearchTerm=""; DesiredPDPColor=; analyticsFacetAttributes=""; MJ_1179_DEDUPE=Affiliate-_-ImpactRadius-_-na-_-116548; _AN_CGID_COOKIE=35556; MJRVI_10000001=254273_product%7C4924369_product%7C6671414_product%7C219880_product%7C6984377_product; _gid=GA1.2.909758962.1657595750; WC_AUTHENTICATION_207354647=207354647%2CDvFqy2qhCrCRd1M%2FGB%2FuAwLbMkmtdSABMdrpVeRNTwI%3D; 90220406_clogin=v=1&l=37738581657595752002&e=1657597554440; _clck=zb9j5e|1|f33|0; __attentive_dv=1; LPSID-9888306=hiynLyYmSjyC4oLh0rFSOA; tfc-l=%7B%22k%22%3A%7B%22v%22%3A%22o1fjup7evd2fqhq5d4jfsjk1kt%22%2C%22e%22%3A1719473962%7D%2C%22c%22%3A%7B%22v%22%3A%22adult%22%2C%22e%22%3A1719473961%7D%2C%22a%22%3A%7B%22v%22%3A%22ce7b473c-b992-4194-a0b7-b46ecc3e797c%22%2C%22e%22%3A1657682167%7D%7D; tfc-s=%7B%22v%22%3A%22tfc-fitrec-product%3D26%22%7D; fs_uid=#mZR#4917820554874880:4676065062096896/1688110748; _gat_UA-9999586-1=1; BVBRANDID=380941b9-a849-4b63-bfa2-fa6b5cfc77d9; BVBRANDSID=38320168-e5fa-453b-a432-696d9d9b897e; fsURL=https://app.fullstory.com/ui/mZR/session/4917820554874880%3A4676065062096896; JSESSIONID=0000EZW4T3Jn9quYly5Uxm1yD4m:-1; WC_USERACTIVITY_207354647=207354647%2C10208%2C0%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C689060808%2Cver_1657595744970%2CuU6rTqGiSOEWq1b%2FN66eCDs5jd7i%2B2joEdZWbwMj6VbIb%2FrQq9Nw4isZnh6Z4AFK89tbPy%2BosYpCQtuRqXx3UQPDU%2BAmlKmuWuVzjbXcjQUq%2B4Fi%2B%2BS9Cw4VuQouNBB9jq7uelymFYAJnL13k9pyThoMihJqLqvB%2F%2B6C2s1B4TCCISpiGZqcRy9yuqg6CqEYlykSLjLGYfUhmLTFYgzNNUo15UKFdxN7gIwfWPwCMOsfhF4f5Tkzo268NCJpXBNw5J8fW8XK6ck0CRl3na0t6g%3D%3D; WC_ACTIVITYDATA_207354647=G%2C-1%2CUSD%2C10000001%2C10011%2C-2000%2C1656574746783-207015%2C-1%2CUSD%2CsZloZhTLG3jnayK81Kndh7Ecw3Fn%2BgemfNpZ4wK3Ao2YW2EgJUsHrLfBjwXEhZ55bVImsC4EL0eogYbilLlGb4lzAI%2F5a8dVCHgDU%2F5ik%2B03UBNk54u%2B5%2BIzA47vf3aM1xo3lNG2n67L1J3aQ9ZeOAY1%2FgYtlVOKhzMtApmH%2B5ASq5zJeJG1dQF1fiMrN%2BUTghfEiF2ssqy1nXXpLssXR9bR7s%2FDP6L6bkZZ%2B4IIUig%3D; cto_bundle=rJ6LfF9NMG9CRkRZeDJsVTdDRlN2M2JSNVM5N0ZhVk9xMlZ3WTRTYWtBTHA5RTFodWR5b041QlE4TXNqaEslMkZoOWYzV3B5WTBncFgycmFVU1lQM0ppWkU4SkJ0VWtrd0pNaXJzMFY1dVlpaWZYNUJwWktXb3RaZG00YWljMiUyRmwwUiUyRmN2RTZFY2tPT0x3OEpTbnN6YTZGa1FoSkElM0QlM0Q; IR_1676=1657629898334%7C0%7C1657629898334%7C%7C; _uetsid=ef3a7ab0019011ed8ddacbf8fd95bfc0; _uetvid=b9fd07f0f84711ec8c678b90de2b8be8; _px3=b62ad38c823c89c7675316bfebac28de03e6838df05fa7ff2e4d80359daa9217:FVq/KY84Y0AnDog+5ze7rS60a/RnhYzRZbRrN4ilojcn77i8WT2lLPfXZ1TevhPyME9wS+eKTjePrF4f49gbjw==:1000:oBcWWOpgSJd0Rbh//e/uVr1sqy1HQJoPELKMVhQmuUbftNVROhfnhUcT3cZ+xuBzmK7moCTo8dvEnPxvIjdn5vduL0stxd4cDCS4OKf+BBQWXGOdF7gAyqXlTuVd0FQ6Mj9TiI0RrwkiU7azWHs60Qq+qEHRg0pKzImwycnF2wI9MEnKUlokBESTT5oSlPD9xv1d+EqeYV3+CFs5VuMQLw==; _clsk=gf64k|1657629900600|2|1|k.clarity.ms/collect; __attentive_pv=1; __attentive_ss_referrer="https://www.moosejaw.com/product/maui-jim-women-s-punchbowl-polarized-sunglasses_10269497"; mt.pevt=mr%3Dt1565286421%26mi%3D\'2.334327528.1656574747974\'%26u%3D\'https://www.moosejaw.com/\'%26e%3D!(xi)%26ii%3D!(\'4,2,64820,,,,1657629894,4,1657629904\')%26eoq%3D!t',
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

def get_crawler(name, cfg, queue, db):
    crawler_class = crawlers.get_crawler_class(name)
    crawler = crawler_class(cfg, queue, db)
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
    crawler = get_crawler(name, crawler_cfg, crawler_queue, db)
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