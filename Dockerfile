# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

WORKDIR /app
# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app && apt-get update && apt-get -y install libcurl4-openssl-dev gcc libssl-dev
USER appuser

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . /app
# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#ENTRYPOINT ["python", "jetrag/cli.py"]
