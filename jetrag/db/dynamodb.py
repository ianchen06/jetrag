import boto3

class DynamodbStore:
    def __init__(self) -> None:
        self.db = boto3.resource('dynamodb')
    
    def put(self, table, data):
        table = self.db.Table(table)
        table.put_item(Item=data)