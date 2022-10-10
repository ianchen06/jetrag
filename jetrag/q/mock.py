class FakeQueue:
    def __init__(self, name):
        self.name = name
        self.q = []

    def get(self):
        self.q.pop()
        return '', ''

    def put(self, msg):
        print(f"[fakequeue] recv: {msg}")
        return self.q.append(msg)

    def done(self, receipt_handle):
        pass