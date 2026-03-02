import os
import sys
from unittest.mock import patch

import boto3
from moto import mock_aws

from ceda_download_tool.main import main


@mock_aws
def test_s3_upload_http(mock_file):
    with patch.dict(os.environ, {"MOTO_S3_CUSTOM_ENDPOINTS": "https://s3.test.com"}):
        s3 = boto3.resource("s3", region_name="us-east-1")
        bucket = "testbucket"
        s3.create_bucket(Bucket=bucket)

        test_args = [
            "main.py",
            "--token",
            "mock-token-abc",
            "--url",
            "https://test.url.ac.uk/dir/file.nc",
            "--dest",
            f"https://{bucket}.s3.test.com/files",
            "--checksum",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        obj = s3.Object(bucket, "files/file.nc")
        uploaded_content = obj.get()["Body"].read()

    assert uploaded_content == b"fake netcdf data"


@mock_aws()
def test_s3_upload_ftp(mock_ftp_server, mock_file):
    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/file.nc"

    with patch.dict(os.environ, {"MOTO_S3_CUSTOM_ENDPOINTS": "https://s3.test.com"}):
        s3 = boto3.resource("s3", region_name="us-east-1")
        bucket = "testbucket"
        s3.create_bucket(Bucket=bucket)

        test_args = [
            "main.py",
            "--username",
            "anonymous",
            "--password",
            "user@email.com",
            "--url",
            url,
            "--dest",
            f"https://{bucket}.s3.test.com/files",
            "--checksum",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        obj = s3.Object(bucket, "files/file.nc")
        uploaded_content = obj.get()["Body"].read()

    assert uploaded_content == b"mocked ftp file.nc"
