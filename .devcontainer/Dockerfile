FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye@sha256:f9687cf8ff930028b32eb2fa7a1cb0b65dbd5180b46e0173faded888bfa14743

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       openjdk-17-jdk \
       curl \
       gnupg \
       build-essential \
       git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH="${JAVA_HOME}/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m pip install --upgrade --no-cache-dir pip setuptools wheel

