import json
import logging
import threading

import pytest
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


@pytest.fixture(autouse=False)
def mock_file(requests_mock):
    file_url = "https://test.url.ac.uk/dir/file.nc"
    return requests_mock.get(file_url, content=b"fake netcdf data", status_code=200)


@pytest.fixture(autouse=False)
def mock_file_2(requests_mock):
    file_url = "https://test.url.ac.uk/dir/file2.nc"
    return requests_mock.get(file_url, content=b"2nd fake netcdf data", status_code=200)


@pytest.fixture(autouse=False)
def mock_directory(requests_mock):
    dir_url = "https://test.url.ac.uk/dir?json"
    content_json = {
        "path": "/dir",
        "items": [
            {
                "path": "dir/file.nc",
                "directory": "/dir",
                "name": "file.nc",
                "last_modified": "2022-07-05T04:20:23.946063",
                "type": "dir",
                "fileset": "spot-45205-highresSST-present",
                "regex_date": "2020-07-29",
            },
        ],
    }

    content_json = json.dumps(content_json)
    return requests_mock.get(dir_url, content=bytes(content_json, "utf-8"), status_code=200)


@pytest.fixture(autouse=False)
def mock_token(requests_mock):
    def _mock_token(status_code=200, response_data=None):
        token_url = "https://services.ceda.ac.uk/api/token/create/"

        if response_data is None:
            response_data = {"access_token": "mock-token-abc"} if status_code == 200 else {"error": "unauthorized"}

        return requests_mock.post(token_url, json=response_data, status_code=status_code)

    return _mock_token


@pytest.fixture
def mock_ftp_server(tmp_path):
    file_content = b"mocked ftp file.nc"
    (tmp_path / "file.nc").write_bytes(file_content)

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


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure logs are reset so there are no conflicts"""
    yield
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()
