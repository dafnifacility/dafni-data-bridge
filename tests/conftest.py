import json
import logging
import os
import threading

import boto3
import pytest
from moto.server import ThreadedMotoServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


@pytest.fixture(autouse=False)
def auth_url(httpserver):
    def _mock_token(status_code=200):
        if status_code == 503:
            httpserver.expect_request("/dir/file.nc").respond_with_data(
                response_data="<html><body><h1>502 Bad Gateway</h1></body></html>",
                status=503,
                content_type="text/html",
            )
        httpserver.expect_request("/api/token/create/").respond_with_json(
            {"error": "unauthorized"} if status_code != 200 else {"access_token": "mock-token-abc"}, status=status_code
        )

        return httpserver

    return _mock_token


@pytest.fixture
def file_url(httpserver):
    def _mock_file(status_code=200):
        if status_code == 200:
            httpserver.expect_request("/dir/file.nc").respond_with_data(
                b"fake netcdf data",
                content_type="application/octet-stream",
            )
        if status_code == 401:
            httpserver.expect_request("/dir/file.nc").respond_with_data(
                content_type="text/html; charset=utf-8",
            )
        if status_code == 503:
            httpserver.expect_request("/dir/file.nc").respond_with_data(
                response_data="<html><body><h1>502 Bad Gateway</h1></body></html>",
                status=503,
                content_type="text/html",
            )
        return httpserver

    return _mock_file


@pytest.fixture
def file_url_2(httpserver):
    httpserver.expect_request("/dir/file2.nc").respond_with_data(
        b"2nd fake netcdf data",
        content_type="application/octet-stream",
    )
    return httpserver


@pytest.fixture(autouse=False)
def mock_ceda_directory(httpserver):
    content_json = {
        "path": "/dir",
        "items": [
            {
                "path": "dir/file.nc",
                "directory": "/dir",
                "name": "file.nc",
                "last_modified": "2022-07-05T04:20:23.946063",
                "type": "file",
                "fileset": "spot-45205-highresSST-present",
                "regex_date": "2020-07-29",
            },
            {
                "path": "dir/file2.nc",
                "directory": "/dir",
                "name": "file2.nc",
                "last_modified": "2022-07-05T04:20:23.946063",
                "type": "file",
                "fileset": "spot-45205-highresSST-present",
                "regex_date": "2020-07-29",
            },
        ],
    }

    content_json = json.dumps(content_json)
    httpserver.expect_request("/dir").respond_with_data(content_json, content_type="application/json", status=200)

    return httpserver


@pytest.fixture
def mock_ftp_server(tmp_path):
    dir_path = tmp_path / "dir/"
    dir_path.mkdir()
    file_content = b"mocked ftp file.nc"
    (dir_path / "file.nc").write_bytes(file_content)
    file_content = b"2nd mocked ftp file.nc"
    (dir_path / "file2.nc").write_bytes(file_content)

    auth = DummyAuthorizer()
    auth.add_user("anonymous", "user@email.com", str(tmp_path), perm="elr")

    handler = FTPHandler
    handler.authorizer = auth

    server = FTPServer(("127.0.0.1", 0), handler)
    port = server.socket.getsockname()[1]

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield "127.0.0.1", port

    server.close_all()


@pytest.fixture(scope="function")
def file_gws_url(httpserver):
    httpserver.expect_request("/dir/file.nc").respond_with_data(
        b"fake netcdf data",
        content_type="application/octet-stream",
    )
    os.environ["GWS_BASE_URL"] = httpserver.url_for("")
    yield httpserver
    # del os.environ["GWS_BASE_URL"]


@pytest.fixture(scope="function")
def file_gws_url_2(httpserver):
    httpserver.expect_request("/dir/file2.nc").respond_with_data(
        b"2nd fake netcdf data",
        content_type="application/octet-stream",
    )
    os.environ["GWS_BASE_URL"] = httpserver.url_for("")
    yield httpserver
    # del os.environ["GWS_BASE_URL"]


@pytest.fixture(scope="function")
def directory_gws_url(httpserver, file_gws_url, file_gws_url_2):
    mock_gws_page = '<html> \
        <head> \
        <title>Index of /dir</title> \
        </head> \
        <body> \
        <h1>Index of /dir</h1> \
        <table> \
        <tr><th valign="top"><img alt="[ICO]" src="/icons/blank.gif"/></th><th><a href="?C=N;O=D">Name</a></th><th>\
            <a href="?C=M;O=A">Last modified</a></th><th> \
                <a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr> \
        <tr><th colspan="5"><hr/></th></tr> \
        <tr><td valign="top"><img alt="[PARENTDIR]" src="/icons/back.gif"/></td> \
            <td><a href="/public/accord/">Parent Directory</a></td><td> </td><td align="right">  - </td><td> \
                </td></tr> \
        <tr><td valign="top"><img alt="[   ]" src="/icons/unknown.gif"/></td>\
            <td><a href="file.nc">T_Pacific_large.nc</a></td> \
            <td align="right">2025-08-08 12:18  </td><td align="right"> 46M</td><td> </td></tr>\
        <tr><td valign="top"><img alt="[   ]" src="/icons/unknown.gif"/></td>\
            <td><a href="file2.nc">T_Pacific_medium.nc</a></td> \
            <td align="right">2025-09-18 11:54  </td><td align="right">591K</td><td> </td></tr>\
        <tr><th colspan="5"><hr/></th></tr>\
        </table>\
        </body></html>'

    httpserver.expect_request("/dir/").respond_with_data(
        mock_gws_page,
        content_type="text/html",
    )
    os.environ["GWS_BASE_URL"] = httpserver.url_for("")
    yield httpserver
    del os.environ["GWS_BASE_URL"]


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure logs are reset so there are no conflicts"""
    yield
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()


@pytest.fixture(scope="function")
def moto_s3_server():
    server = ThreadedMotoServer()
    server.start()

    s3 = boto3.resource(
        "s3",
        region_name="us-east-1",
        endpoint_url="http://localhost",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    s3.create_bucket(Bucket="testbucket")

    yield s3
    server.stop()
