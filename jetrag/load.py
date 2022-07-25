import logging
import threading
import multiprocessing as mp
import traceback
import sys
import queue

from sqlalchemy import select

from parsers.moosejaw import MoosejawParser
from loaders.moosejaw import MoosejawLoader
from models.moosejaw import *
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

def get_html_worker(name, in_q, out_q, done_q):
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt) 
    for filename in iter(in_q.get, None):
        logger.info(f"[get_html_worker{name}] Doing {filename}")
        out_q.put(c.db.get(filename))
    done_q.put(f"[get_html_worker{name}] DONE")

def parse_worker(name, in_q, out_q, done_q):
    parser = MoosejawParser()
    for html in iter(in_q.get, None):
        logger.info(f"[parse_worker{name}] Doing")
        try:
            out_q.put(parser.parse(html))
        except Exception as e:
            tb = traceback.format_exc()
            #logger.error(tb)
            done_q.put(f"[parse_worker{name}] {e}: {tb}")
    done_q.put(f"[parse_worker{name}] DONE")

def load_worker(name, in_q, done_q):
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt) 
    for products in iter(in_q.get, None):
        if not products:
            continue
        logger.info(f"[load_worker{name}] Doing {products[0]['item_code']}")
        try:
            c.load([products])
        except Exception as e:
            logger.error(str(e))
            if "key 'PRIMARY'" in str(e):
                logger.info("Duplicate primary key, skipping")
                continue
            tb = traceback.format_exc()
            #logger.error(tb)
            done_q.put(f"[load_worker{name}] {e}: {tb}")
    done_q.put(f"[load_worker{name}] DONE")


if __name__ == '__main__':
    s3 = S3Store('jetrag3', '')
    c = MoosejawLoader(CONNSTR, s3, dt)

    filenames_all = c.get()

    # DEBUG
    #filenames_all = [x for x in filenames_all if '10409428' in x] + filenames_all
    page_size = 500
    page = 0
    item_codes = []
    while True:
        res = c.session.query(Item.item_code).limit(page_size).offset(page*page_size)
        to_add = [row.item_code for row in res]
        if not to_add:
            break
        item_codes += to_add
        page += 1

    item_codes = set(item_codes)
    logger.info(len(item_codes))

    logger.info(f"total filenames: {len(filenames_all)}")
    filenames_all = [x for x in filenames_all if int(x.split('_')[1].replace('.html', '')) not in item_codes]
    logger.info(f"total filenames: {len(filenames_all)}")

    done_q = mp.Queue()

    # get_html
    get_html_in_q = mp.Queue()
    get_html_out_q = mp.Queue()
    get_html_threads = [threading.Thread(
        target=get_html_worker,
        args=(thread_id, get_html_in_q, get_html_out_q, done_q),
        daemon=True
    ) for thread_id in range(2)]
    for t in get_html_threads:
        t.start()
    
    # parser
    parser_in_q = get_html_out_q
    parser_out_q = mp.Queue()
    processes = [mp.Process(
        target=parse_worker,
         args=(process_id, parser_in_q, parser_out_q, done_q)
         ) for process_id in range(3)]
    for p in processes:
        p.start()

    # to_db
    loader_in_q = parser_out_q
    loader_threads = [threading.Thread(
        target=load_worker,
        args=(thread_id, loader_in_q, done_q),
        daemon=True
    ) for thread_id in range(20)]
    for t in loader_threads:
        t.start()

    for filename in filenames_all:
        get_html_in_q.put(filename)
    for t in get_html_threads:
        get_html_in_q.put(None)

    cnt = {
        'get_html': 2,
        'parse': 3,
        'load': 20,
    }
    while True:
        msg = done_q.get()
        if msg.endswith('DONE'):
            logger.info(msg)
            if 'get_html' in msg:
                cnt['get_html'] -= 1
                if cnt['get_html'] == 0:
                    logger.info("all get_html done")
                    for p in processes:
                        parser_in_q.put(None)
            if 'parse' in msg:
                cnt['parse'] -= 1
                if cnt['parse'] == 0:
                    logger.info("all parse done")
                    for t in loader_threads:
                        loader_in_q.put(None)
            if 'load' in msg:
                cnt['load'] -= 1
                if cnt['load'] == 0:
                    logger.info("all load done, brekaing out control loop")
                    break
        else:
            logger.error("CAUGHT ERROR")
            logger.error(msg)
            for row in iter(get_html_in_q.get, None):
                pass
            for t in get_html_threads:
                get_html_in_q.put(None)
            for p in processes:
                parser_in_q.put(None)
            for t in loader_threads:
                loader_in_q.put(None)
            

    logger.info("waiting to exit cleanly")
    for w in get_html_threads+processes+loader_threads:
        #logger.info(f"waiting for {w} to exit")
        w.join()
        #logger.info(f"{w} exited")
    logger.info("all exited")
    for q in [get_html_in_q, get_html_out_q, parser_in_q, parser_out_q, loader_in_q, done_q]:
        q.cancel_join_thread()