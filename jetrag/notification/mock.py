import json

from http_client import HTTPDriver

class FakeNotifier:
    def __init__(self):
        pass

    def send(self, data):
        pass

    def send_info(self, data):
        pass