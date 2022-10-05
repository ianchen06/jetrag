import random

import requests

class HTTPDriver:
    def __init__(self):
        self.session = requests.Session()
        self.ua_list = [
            #"Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            #"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:88.0) Gecko/20100101 Firefox/88.0",
            #"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        ]
    
    def request_with_random_ua(self, method, url, **kwargs):
        ua = random.choice(self.ua_list)
        kwargs['headers']['User-Agent'] = ua
        return requests.request(method, url, **kwargs)
