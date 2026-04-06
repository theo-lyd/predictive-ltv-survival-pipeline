FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk curl gnupg build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN python -m pip install --upgrade pip

