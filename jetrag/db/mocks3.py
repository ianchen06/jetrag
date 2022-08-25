class FakeS3Store:
    def __init__(self):
        pass

    def put(self, table, data):
        print(f"table: {table}")
        print(f"data: {data}")

    def list(self, table):
        pass

    def get(self, key):
        pass
        