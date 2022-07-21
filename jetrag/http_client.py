import random

import requests

class HTTPDriver:
    def __init__(self):
        self.session = requests.Session()
        self.ua_list = [x.strip() for x in open('./jetrag/ua.txt').readlines()]
    
    def request_with_random_ua(self, method, url, **kwargs):
        ua = random.choice(self.ua_list)
        kwargs['headers']['User-Agent'] = ua
        print(kwargs)
        return requests.request(method, url, **kwargs)
