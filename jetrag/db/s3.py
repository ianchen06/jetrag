import io
import json

import boto3

class S3Store:
    def __init__(self, db, base_path):
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(db)
        self.base_path = base_path

    def put(self, table, data):
        d = data['html']
        filename = data['url'].split('/')[-1]
        path = f"{table}/{filename}.html"
        if self.base_path:
            path = self.base_path + "/" + path
        self.bucket.upload_fileobj(io.BytesIO(d.encode('utf-8')), path)

    def list(self, table):
        return [x for x in self.bucket.objects.filter(Prefix=table)]

    def get(self, key):
        buf = io.BytesIO()
        self.bucket.download_fileobj(key, buf)
        return buf.getvalue().decode('utf-8')
        