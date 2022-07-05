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
        msgs = self.client.receive_message(QueueUrl=self.q, WaitTimeSeconds=20)
        if 'Messages' in msgs:
            for msg in msgs['Messages']:
                self.client.delete_message(QueueUrl=self.q, ReceiptHandle=msg['ReceiptHandle'])
        return msgs

    def put(self, msg):
        return self.client.send_message(QueueUrl=self.q, MessageBody=json.dumps(msg))