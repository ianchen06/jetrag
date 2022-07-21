import logging
import threading
import multiprocessing as mp
import sys

from parsers.moosejaw import MoosejawParser
from loaders.moosejaw import MoosejawLoader
from db.s3 import S3Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONNSTR = (
    'mysql+auroradataapi://:@/moosejaw?'
    'aurora_cluster_arn=arn:aws:rds:ap-northeast-1:068993006585:cluster:jetrag3'
    '&secret_arn=arn:aws:secretsmanager:ap-northeast-1:068993006585:secret:rds-db-credentials/cluster-YXGYNX2ORLFS6RYDNGEBFTMHHA/jetrag-PvBX2f'
)

dt = sys.argv[1]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_html_worker(name, in_q, out_q):
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt) 
    for filename in iter(in_q.get, None):
        logger.info(f"[get_html_worker{name}] Doing {filename}")
        out_q.put(c.db.get(filename))

def parse_worker(name, in_q, out_q):
    parser = MoosejawParser()
    for html in iter(in_q.get, None):
        logger.info(f"[parse_worker{name}] Doing")
        out_q.put(parser.parse(html))

def load_worker(name, in_q):
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt) 
    for products in iter(in_q.get, None):
        logger.info(f"[load_worker{name}] Doing {products[0]['item_code']}")
        c.load([products])

if __name__ == '__main__':
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt)

    filenames_all = c.get()

    # DEBUG
    #filenames_all = [x for x in filenames_all if 'du-er-men-s-no-sweat-slim-fit-pant_10357077' in x]

    logger.info(f"total filenames: {len(filenames_all)}")

    # get_html
    get_html_in_q = mp.Queue()
    get_html_out_q = mp.Queue()
    get_html_threads = [threading.Thread(
        target=get_html_worker,
        args=(thread_id, get_html_in_q, get_html_out_q,),
        daemon=True
    ) for thread_id in range(2)]
    for t in get_html_threads:
        t.start()
    
    # parser
    parser_in_q = get_html_out_q
    parser_out_q = mp.Queue()
    processes = [mp.Process(
        target=parse_worker,
         args=(process_id, parser_in_q, parser_out_q,)
         ) for process_id in range(3)]
    for p in processes:
        p.start()

    # to_db
    loader_in_q = parser_out_q
    loader_threads = [threading.Thread(
        target=load_worker,
        args=(thread_id, loader_in_q,),
        daemon=True
    ) for thread_id in range(20)]
    for t in loader_threads:
        t.start()

    for filename in filenames_all:
        get_html_in_q.put(filename)
    for t in get_html_threads:
        get_html_in_q.put(None)
    for t in get_html_threads:
        t.join()

    for p in processes:
        parser_in_q.put(None)
    for p in processes:
        p.join()

    for t in loader_threads:
        loader_in_q.put(None)
    for t in loader_threads:
        t.join()
