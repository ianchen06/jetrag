import boto3

from driver import Driver


class EcsDriver(Driver):
    def __init__(self, cfg, name):
        self.cfg = cfg
        self.name = name
        self.client = boto3.client('ecs')

    def launch(self):
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
                        'command': ['worker', 'start', self.name]
                    }
                ]
            },
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