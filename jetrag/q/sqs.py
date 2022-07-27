import json

import boto3

class Sqs:
    def __init__(self):
        self.client = boto3.client('sqs')

    def create_queue(self, name):
        return self.client.create_queue(QueueName=name)

    def list_queues(self):
        return self.client.list_queues(MaxResults=1000)

class SqsQueue:
    def __init__(self, name):
        self.name = name
        self.client = boto3.client('sqs')
        self.q = self.client.get_queue_url(QueueName=name)['QueueUrl']

    def get(self):
        """return one message from SQS

        :return: Message
        :rtype: dict
        """
        res = self.client.receive_message(
            QueueUrl=self.q,
            WaitTimeSeconds=20,
            VisibilityTimeout=30,
            MaxNumberOfMessages=1
        )
        if 'Messages' in res:
            msgs = res['Messages']
            if msgs:
                return json.loads(msgs[0]['Body'])

    def put(self, msg):
        return self.client.send_message(QueueUrl=self.q, MessageBody=json.dumps(msg))

    def done(self, msg):
        self.client.delete_message(QueueUrl=self.q, ReceiptHandle=msg['ReceiptHandle'])