import json

from http_client import HTTPDriver

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.http_client = HTTPDriver()

    def send(self, data):
        self.http_client.session.request('POST',
        url=self.webhook_url,
        data=json.dumps(data))