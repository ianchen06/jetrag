import json

import redis

class RedisStore:
    def __init__(self):
        self.client = redis.Redis()

    def put(self, table, data):
        self.client.set(data['url'], json.dumps(data))