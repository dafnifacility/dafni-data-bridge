import os
import subprocess


# @mock_aws
def test_s3_upload_http(file_url, auth_url, moto_s3_server):
    auth_url(200)
    file = file_url(200)

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--token",
            "mock-token-abc",
            "--url",
            file.url_for("/dir/file.nc"),
            "--dest",
            "http://testbucket.s3.localhost/files/",
            "--checksum",
        ],
        env={
            **os.environ,
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
            "AWS_ENDPOINT_URL": "http://localhost",
        },
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    print(result.stderr)
    obj = moto_s3_server.Object("testbucket", "files/file.nc")
    uploaded_content = obj.get()["Body"].read()

    assert uploaded_content == b"fake netcdf data"


# @mock_aws()
# def test_s3_upload_ftp(mock_ftp_server, mock_file):
#     host, port = mock_ftp_server
#     url = f"ftp://{host}:{port}/file.nc"

#     with patch.dict(os.environ, {"MOTO_S3_CUSTOM_ENDPOINTS": "https://s3.test.com"}):
#         s3 = boto3.resource("s3", region_name="us-east-1")
#         bucket = "testbucket"
#         s3.create_bucket(Bucket=bucket)

#         test_args = [
#             "main.py",
#             "--username",
#             "anonymous",
#             "--password",
#             "user@email.com",
#             "--url",
#             url,
#             "--dest",
#             f"https://{bucket}.s3.test.com/files",
#             "--checksum",
#         ]

#         with patch.object(sys, "argv", test_args):
#             main()

#         obj = s3.Object(bucket, "files/file.nc")
#         uploaded_content = obj.get()["Body"].read()

#     assert uploaded_content == b"mocked ftp file.nc"
