from config import get_config
from db.s3 import S3Store
from q.sqs import SqsQueue

cfg = get_config("prod")

s3 = S3Store(cfg["html_store"]["s3"])
q = SqsQueue("jetrag3-sqs-zappos")

files = s3.list("backcountry/20221128")
print(f"total {len(files)} files")
for filename in files:
    pass
    # q.put({"method": "get_html_from_html_store", "args": [filename]})
