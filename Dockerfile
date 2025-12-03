FROM python:3.13-slim

RUN apt-get update && apt-get install -y graphviz

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

COPY . /workspace/

EXPOSE 6699
