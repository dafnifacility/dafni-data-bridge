FROM python:3.12-slim

WORKDIR /src

COPY ceda_download_tool-0.1.4-py3-none-any.whl /src/ceda_download_tool-0.1.4-py3-none-any.whl

RUN pip install --no-cache-dir --upgrade pip && \
    pip install /src/ceda_download_tool-0.1.4-py3-none-any.whl --no-cache-dir

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]