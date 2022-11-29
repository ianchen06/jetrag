import concurrent.futures

from config import get_config
from db.s3 import S3Store
from q.sqs import SqsQueue

cfg = get_config("prod")

#s3 = S3Store(cfg["html_store"]["s3"])
q = SqsQueue("jetrag3-sqs-backcountry")

#files = s3.list("backcountry/20221128")
#print(f"total {len(files)} files")
urls = []
with open('/tmp/data/all_uniq.txt') as f:
    for l in f:
        urls.append(l.strip())

print(f"publishing {len(urls)} products")

def pub(url):
    q.put({"method": "get_product", "args": ['https://www.backcountry.com'+url]})

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(pub, url): url for url in urls}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        print(url)
    
