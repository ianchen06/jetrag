TAG := $(shell date +%s)
REPO_URI := 068993006585.dkr.ecr.us-east-2.amazonaws.com/jetrag3-crawler
AURORA_ARN := arn:aws:rds:us-east-2:068993006585:cluster:jetrag3
AURORA_SECRET_ARN := arn:aws:secretsmanager:us-east-2:068993006585:secret:rds-db-credentials/cluster-3B7R2LQNCTJACT24IDJADOZ5MY/jetrag/1664344911948-bFMGbz 
login:
	aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 068993006585.dkr.ecr.us-east-2.amazonaws.com

build:
	docker build -t ${REPO_URI}:${TAG} . && docker push ${REPO_URI}:${TAG} && docker tag ${REPO_URI}:${TAG} ${REPO_URI}:latest

register:
	aws ecs register-task-definition --cli-input-json fileb://jetrag/aws_manifests/jetrag3-crawler-task-definition.json

register-prod:
	aws ecs register-task-definition --cli-input-json fileb://jetrag/aws_manifests/jetrag3-crawler-task-definition_prod.json

model-gen:
	#sqlacodegen --noviews --noconstraints --noindexes --outfile ./jetrag/models/backcountry.py 'mysql+auroradataapi://:@/backcountry?aurora_cluster_arn=${AURORA_ARN}&secret_arn=${AURORA_SECRET_ARN}'
	sqlacodegen --noviews --outfile ./jetrag/models/backcountry.py 'mysql+auroradataapi://:@/backcountry?aurora_cluster_arn=${AURORA_ARN}&secret_arn=${AURORA_SECRET_ARN}'

.PHONY: login build model-gen

