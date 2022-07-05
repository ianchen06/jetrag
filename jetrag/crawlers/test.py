import logging
import random

from driver import HTTPDriver
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
        if is_error(0.3):
            raise Exception("page invalid")
        if is_error(0.3):
            raise BadIP("1.2.3.4")
        self.store('', {'url': url, 'html': url})

    def store(self, url, data):
        self.db.put('test', data)