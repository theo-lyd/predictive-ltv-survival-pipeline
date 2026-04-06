FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk curl gnupg \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN python -m pip install --upgrade pip \
    && pip install dbt-databricks databricks-cli pyspark==3.5.1 great-expectations pandas numpy faker streamlit plotly apache-airflow
