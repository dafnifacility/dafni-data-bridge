FROM python:3.12-slim
WORKDIR /src

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "git+https://github.com/dafnifacility/dataset-download-tool.git"

RUN mkdir -p /data/outputs

COPY dl.py dl.py

CMD ["python", "dl.py"]