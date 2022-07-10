import logging
import random
import time

from http_client import HTTPDriver
from errors import BadIP

logger = logging.getLogger(__name__)

def is_error(freq=0.3):
    return random.randrange(100) < (freq * 100)

class Test:
    def __init__(self, cfg, queue, db):
        self.cfg = cfg
        self.queue = queue
        self.db = db
        self.http = HTTPDriver()

    def dispatch(self):
        logger.info('disatching job')
        self.queue.put({'method': 'first'})

    def first(self):
        result = ["http://example%s.com"%x for x in range(10)]
        for url in result:
            self.queue.put({'method': 'second', 'args': [url]})
        return result
    
    def second(self, url):
        time.sleep(random.randint(1, 3))
        if is_error(0.1):
            raise Exception("page invalid")
        if is_error(0):
            raise BadIP("1.2.3.4")
        self.store({'url': url, 'html': url})
        return {'url': url, 'html': url}

    def store(self, data):
        self.db.put('test', data)