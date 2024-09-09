FROM python:3.12.4-slim-bookworm

ARG DEBIAN_FRONTEND="noninteractive"
ARG ROOT_PATH
ARG BROKER
ARG TOPIC

WORKDIR /rorschach_collector

COPY rorschach_collector /rorschach_collector/rorschach_collector
COPY requirements.txt /rorschach_collector
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "rorschach_collector"]
