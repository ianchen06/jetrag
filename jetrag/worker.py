import json

class Worker:
    def __init__(self, crawler):
        self.crawler = crawler

    def start(self):
        while True:
            msgs = self.crawler.queue.get()
            print(msgs)
            if 'Messages' in msgs:
                for msg in msgs['Messages']:
                    d = json.loads(msg['Body'])
                    func = getattr(self.crawler, d['method'])
                    res = func(*d.get('args', []), **d.get('kwargs', {}))
                    print(res)