FROM python:3.12-slim
WORKDIR /src

ARG GITHUB_TOKEN

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=secret,id=github_token \
    pip install "git+https://$(cat /run/secrets/github_token)@github.com/dafnifacility/dataset-download-tool.git"

RUN mkdir -p /data/outputs

COPY download_model.py download_model.py

CMD ["python", "download_model.py"]