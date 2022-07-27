import logging
import traceback
import atexit
import sys
import signal

import requests

logger = logging.getLogger(__name__)
class Worker:
    def __init__(self, cfg, crawler, driver, notifier, metadb):
        self.cfg = cfg
        self.crawler = crawler
        self.driver = driver
        self.notifier = notifier
        self.metadb = metadb
        self.num_job_succeeded = 0
        self.timeout_secs = 30
        atexit.register(self.cleanup)
        signal.signal(signal.SIGALRM, self.handle_alarm_signal)

    def cleanup(self):
        logger.info('exiting...')
    
    def restart(self):
        logger.info("restarting...")
        self.driver.launch()
        sys.exit(1)

    def handle_alarm_signal(self, signum, frame):
        logger.info("timeout waiting for tasks from queue")
        self.notifier.send({'text': 'timeout waiting for tasks from queue'})
        sys.exit(1)

    def handle_error(self, tb):
        error_msg = f"{tb}\n{self.num_job_succeeded}"
        logger.error(error_msg)
        self.notifier.send({'text': error_msg})
        self.restart()

    def start_shutdown_timer(self):
        logger.debug("starting shutdown timer")
        signal.alarm(self.timeout_secs)

    def stop_shutdown_timer(self):
        signal.alarm(0)

    def start(self):
        public_ip = requests.get('https://api.ipify.org')
        logger.info(f"public_ip is {public_ip.text}")
        self.start_shutdown_timer()
        while True:
            # this line will block
            msg = self.crawler.queue.get()
            logger.debug("got msg")
            self.stop_shutdown_timer()
            logger.info(msg)
            try:
                # get method from crawler and execute with args/kwargs
                func = getattr(self.crawler, msg['method'])
                res = func(*msg.get('args', []), **msg.get('kwargs', {}))
                
                # job succeed
                self.num_job_succeeded += 1
                logger.info(f"success: {res}")
                self.start_shutdown_timer()
            except Exception as e:
                tb = traceback.format_exc()
                self.handle_error(f"{tb}\n{e}")
