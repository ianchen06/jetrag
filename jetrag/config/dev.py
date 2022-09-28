import os

cfg = {
    'env': 'dev',
    'manager': {
        'url': 'https://3pf3bma4qf.execute-api.us-east-2.amazonaws.com/dev',
        'token': os.getenv("JETRAG_MANAGER_TOKEN", '')
    },
    'queue': {
        'type': 'sqs',
        'name_template': 'jetrag3-crawler-sqs-dev'
    },
    'worker': {
        'restart': True
    },
    'driver': {
        'type': 'ecs',
        'ecs': {
            'cluster_name': 'jetrag3-cluster',
            'container_name': 'jetrag3',
            'count': 1,
            'task_definition': 'jetrag3-crawler-dev',
            'task_role_arn': 'arn:aws:iam::068993006585:role/jetrag3-crawler-ecs-task-role',
            'subnet_id': 'subnet-00d159d3664c3377f',
            'security_group': 'sg-0f4df8482baf1b9a2'
        }
    },
    'notifications': {
        'type': 'slack',
        'slack': {
            'info_webhook_url': os.getenv('INFO_SLACK_WEBHOOK_URL'), 
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
        }
    },
    'html_store': {
        'type': 's3',
        's3': {
            'bucket_name': 'jetrag3',
            'base_path': ''            
        }
    },
    'db': {
        'sqlalchemy': {
            #'conn_str': 'mysql+pymysql://root:mysql@localhost:3306',
            'conn_str': 'mysql+auroradataapi://:@',
            'aws_access_key_id': os.getenv("RDS_AWS_ACCESS_KEY_ID", ""),
            'aws_secret_access_key': os.getenv("RDS_AWS_SECRET_ACCESS_KEY", ""),
            'connect_args': {
                'aurora_cluster_arn': 'arn:aws:rds:us-east-2:068993006585:cluster:jetrag3',
                'secret_arn': 'arn:aws:secretsmanager:us-east-2:068993006585:secret:rds-db-credentials/cluster-3B7R2LQNCTJACT24IDJADOZ5MY/jetrag/1664344911948-bFMGbz',
            }
        }
    },
    'test': {},
    'zappos': {
        'notifications': {
            'type': 'slack',
            'slack': {
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                'info_webhook_url': os.getenv('ZAPPOS_INFO_SLACK_WEBHOOK_URL'),
            }
        },
        'concurrency': 20,
        'base_url': 'https://www.zappos.com',
        'headers': {
            'authority': 'www.zappos.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity', # no gzip
            'pragma': 'no-cache',
            'referer': 'https://www.zappos.com/',
            'upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:88.0) Gecko/20100101 Firefox/88.0',
        }
    },
    'moosejaw': {
        'notifications': {
            'type': 'slack',
            'slack': {
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                'info_webhook_url': os.getenv('MOOSEJAW_INFO_SLACK_WEBHOOK_URL'),
            }
        },
        'concurrency': 20,
        'base_url': 'https://moosejaw.com',
        'headers': {
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Host': 'www.moosejaw.com',
                'TE': 'Trailers',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:88.0) Gecko/20100101 Firefox/88.0',
        },
    }
}