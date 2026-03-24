FROM python:3.12-slim
ENV ISDAFNI=True
WORKDIR /src

COPY dataset_download_tool-0.1.4-py3-none-any.whl /src/dataset_download_tool-0.1.4-py3-none-any.whl

RUN pip install --no-cache-dir --upgrade pip && \
    pip install /src/dataset_download_tool-0.1.4-py3-none-any.whl --no-cache-dir

RUN rm dataset_download_tool-0.1.4-py3-none-any.whl

RUN mkdir -p /data/outputs

COPY download_model.py download_model.py

CMD ["python", "download_model.py"]