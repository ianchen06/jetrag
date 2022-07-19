login:
	aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 068993006585.dkr.ecr.ap-northeast-1.amazonaws.com

build:
	export REPO_URI=068993006585.dkr.ecr.ap-northeast-1.amazonaws.com/jetrag3-crawler; export TAG=$(date +%s); docker build -t ${REPO_URI}:${TAG} . && docker push ${REPO_URI}:${TAG}

model-gen:
	sqlacodegen --noviews --noconstraints --noindexes --outfile ./jetrag/models/moosejaw.py 'mysql+auroradataapi://:@/moosejaw?aurora_cluster_arn=arn:aws:rds:ap-northeast-1:068993006585:cluster:jetrag3&secret_arn=arn:aws:secretsmanager:ap-northeast-1:068993006585:secret:rds-db-credentials/cluster-YXGYNX2ORLFS6RYDNGEBFTMHHA/jetrag-PvBX2f'

.PHONY: login build model-gen

