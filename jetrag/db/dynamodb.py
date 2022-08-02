import boto3

class Dynamodb:
    def __init__(self, table):
        self.client = boto3.resource('dynamodb')
        self.table = self.client.Table(table)

    def get(self, pk):
        return self.table.get_item(Key={
            'pk': pk
        })

    def put(self, pk, attr, value):
        item = {
            "pk": pk,
            attr: value,
        }
        return self.table.put_item(Item=item)

    def update(self, **kwargs):
        return self.table.update_item(**kwargs)