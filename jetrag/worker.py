import logging
import traceback
import atexit
import sys
import signal

logger = logging.getLogger(__name__)
class Worker:
    def __init__(self, cfg, crawler, driver):
        self.cfg = cfg
        self.crawler = crawler
        self.driver = driver
        self.msgs = []
        self.num_job_succeeded = 0
        self.timeout_secs = 30
        atexit.register(self.cleanup)
        signal.signal(signal.SIGALRM, self.handle_alarm_signal)

    def cleanup(self):
        logger.info('exiting...')
        # put leftover msgs in cache back into queue
        [self.crawler.queue.put(msg) for msg in self.msgs] 
    
    def restart(self):
        logger.info("restarting...")
        self.driver.launch()
        sys.exit(1)

    def handle_alarm_signal(self, signum, frame):
        logger.info("timeout waiting for tasks from queue")
        sys.exit(1)

    def handle_error(self, tb):
        logger.error(tb)
        self.restart()

    def start_shutdown_timer(self):
        logger.info("starting shutdown timer")
        signal.alarm(self.timeout_secs)

    def stop_shutdown_timer(self):
        signal.alarm(0)

    def start(self):
        self.start_shutdown_timer()
        while True:
            # this line will block
            self.msgs = self.crawler.queue.get()
            while self.msgs:
                logger.info("got msg")
                self.stop_shutdown_timer()
                logger.info(self.msgs)
                try:
                    # peek the last msg in cache
                    msg = self.msgs[-1]

                    # get method from crawler and execute with args/kwargs
                    func = getattr(self.crawler, msg['method'])
                    res = func(*msg.get('args', []), **msg.get('kwargs', {}))
                    
                    # job succeed
                    # remove the msg from cache
                    self.msgs.pop()
                    self.num_job_succeeded += 1
                    logger.info(f"success: {res}")
                    self.start_shutdown_timer()
                except Exception as e:
                    tb = traceback.format_exc()
                    self.handle_error(f"{tb}\n{e}")
