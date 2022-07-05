import json
import time

import redis

class RedisQueue:
    def __init__(self, name):
        self.name = name
        self.client = redis.Redis()

    def get(self):
        d = self.client.blpop(self.name)
        return [json.loads(d[1])]

    def put(self, msg):
        return self.client.rpush(self.name, json.dumps(msg))