from cgitb import handler
import logging
import traceback
import atexit
import sys

logger = logging.getLogger(__name__)
class Worker:
    def __init__(self, crawler):
        self.crawler = crawler
        self.msgs = []
        atexit.register(self.shutdown)

    def shutdown(self):
        self.handle_error(self.msgs, 'shutdown...')

    def handle_error(self, msgs, tb):
        logger.error(f"{msgs}\n{tb}")
        [self.crawler.queue.put(msg) for msg in msgs]
        sys.exit(1)

    def start(self):
        while True:
            self.msgs = self.crawler.queue.get()
            while self.msgs:
                logger.info(self.msgs)
                try:
                    msg = self.msgs[-1]
                    func = getattr(self.crawler, msg['method'])
                    res = func(*msg.get('args', []), **msg.get('kwargs', {}))
                    self.msgs.pop()
                    logger.info(res)
                except Exception as e:
                    tb = traceback.format_exc()
                    self.handle_error(self.msgs, tb)
