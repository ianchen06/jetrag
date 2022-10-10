import sys
import argparse

import boto3


client = boto3.client('ecs')
res = client.list_tasks(
    cluster='jetrag3-cluster',
    )
task_arns = res['taskArns']
res = client.describe_tasks(cluster='jetrag3-cluster', tasks=task_arns, include=['TAGS'])

def main(args):
    crawler_name = args.crawler
    action = args.action
    for task in res['tasks']:
        for kv in task['tags']:
            if kv['key'] == 'crawler':
                if kv['value'] == crawler_name:
                    print(task['taskArn'], task['tags'])
                    if action == 'delete':
                        print(f"Deleteing...")
                        client.stop_task(cluster='jetrag3-cluster', task=task['taskArn'])
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='manage ECS tasks')
    parser.add_argument('-c', '--crawler',
                        help='The crawler name, e.g. moosejaw',
                        required=True)
    parser.add_argument('-a', '--action',
                        help='The action to do, e.g. list, delete',
                        required=True)
    args = parser.parse_args()
    sys.exit(main(args))
