import requests

class HTTPDriver:
    def __init__(self):
        self.session = requests.Session()