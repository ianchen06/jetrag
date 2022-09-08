import boto3

from driver import Driver


class EcsDriver(Driver):
    def __init__(self, cfg, name, environment={}):
        self.cfg = cfg
        self.environment = environment
        self.name = name
        self.client = boto3.client('ecs')

    def launch(self, command=[]):
        if not command:
            command = ['python', 'jetrag/cli.py', 'worker', 'start', self.name]
        return self.client.run_task(
            taskDefinition=self.cfg['task_definition'],
            launchType='FARGATE',
            cluster=self.cfg['cluster_name'],
            platformVersion='LATEST',
            count=self.cfg['count'],
            overrides={
                'taskRoleArn': self.cfg['task_role_arn'],#'arn:aws:iam::395407004311:role/jetrag-ecs-task-role',
                'containerOverrides': [
                    {
                        'name': self.cfg['container_name'],
                        'command': command,
                        'environment': self.environment,
                    }
                ]
            },
            tags=[
                {
                    'key': 'crawler',
                    'value': self.name
                }
            ],
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        self.cfg['subnet_id'],
                    ],
                    'assignPublicIp': 'ENABLED',
                    'securityGroups': [self.cfg['security_group']]
                }
            }
        )

    def terminate(self):
        pass

    def relaunch(self):
        pass