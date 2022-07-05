import logging
import traceback

from errors import BadIP

logger = logging.getLogger(__name__)
class Worker:
    def __init__(self, crawler):
        self.crawler = crawler

    def handle_error(self, msg, tb):
        logger.error(f"{msg}\n{tb}")
    
    def handle_bad_ip(self, msg, tb):
        logger.info("switching ip")
        logger.info(f"{msg}\n{tb}")

    def start(self):
        while True:
            msgs = self.crawler.queue.get()
            logger.debug(msgs)
            for msg in msgs:
                func = getattr(self.crawler, msg['method'])
                try:
                    res = func(*msg.get('args', []), **msg.get('kwargs', {}))
                    logger.debug(res)
                except BadIP as e:
                    self.handle_bad_ip(msg, '')
                except Exception as e:
                    tb = traceback.format_exc()
                    self.handle_error(msg, tb)