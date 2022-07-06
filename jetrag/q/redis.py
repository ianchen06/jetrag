import json
from shutil import get_unpack_formats
import time

import redis

class RedisQueue:
    def __init__(self, name):
        self.name = name
        self.client = redis.Redis()

    def get(self):
        return self.get_multi()
        d = self.client.blpop(self.name)
        return [json.loads(d[1])]

    def get_multi(self):
        res = []
        for x in range(3):
            time.sleep(0.1)
            d = self.client.lpop(self.name)
            if d:
                res.append(json.loads(d))
        return res

    def put(self, msg):
        return self.client.rpush(self.name, json.dumps(msg))