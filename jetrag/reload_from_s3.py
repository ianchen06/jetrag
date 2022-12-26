import argparse
import sys

from config import get_config
from db.s3 import S3Store
from q.sqs import SqsQueue

cfg = get_config("prod")

s3 = S3Store(cfg["html_store"]["s3"])
parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['count', 'dispatch'])
parser.add_argument('crawler')
parser.add_argument('dt')
args = parser.parse_args()

q = SqsQueue(f"jetrag3-sqs-{args.crawler}")

files = s3.list(f"{args.crawler}/{args.dt}")
print(f"total {len(files)} files")
if args.mode == 'count':
    sys.exit()
print("dispatching")
for filename in files:
    q.put({"method": "get_html_from_html_store", "args": [filename]})
