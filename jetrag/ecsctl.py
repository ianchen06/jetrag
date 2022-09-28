import sys

import boto3


client = boto3.client('ecs')
res = client.list_tasks(
    cluster='jetrag3-cluster',
    )
task_arns = res['taskArns']
res = client.describe_tasks(cluster='jetrag3-cluster', tasks=task_arns, include=['TAGS'])

for task in res['tasks']:
    for kv in task['tags']:
        if kv['key'] == 'crawler':
            if kv['value'] == sys.argv[1]:
                print(task['taskArn'], task['tags'])
                #client.stop_task(cluster='jetrag3-cluster', task=task['taskArn'])
    
