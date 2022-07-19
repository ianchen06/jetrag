from jetrag.db.dynamodb import Dynamodb

def test_dynamodb_put():
    db = Dynamodb()
    db.put("moosejaw", {"url": "https://moosejaw.com/asdfas", "data": "asdfasdfasd"})