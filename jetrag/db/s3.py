import io
import json

import boto3

class S3Store:
    def __init__(self, db):
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(db)

    def put(self, table, data):
        d = data['html']
        filename = data['url'].split('/')[-1]
        self.bucket.upload_fileobj(io.BytesIO(d.encode('utf-8')), f"{table}/{filename}.html")