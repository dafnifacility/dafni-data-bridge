import sys
from unittest.mock import patch

import pytest
from main import main


def test_token_auth(mock_token, mock_file, requests_mock, tmp_path):
    mock_token(200)
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    test_args = [
        "main.py",
        "--token",
        "mock-token-abc",
        "--url",
        "https://test.url.ac.uk/dir/file.nc",
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    file_request = requests_mock.request_history[0]

    assert file_request.headers["Authorization"] == "Bearer mock-token-abc"


def test_auth_login(mock_token, mock_file, requests_mock, tmp_path):
    mock_token(200)
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    test_args = [
        "main.py",
        "--username",
        "testuser",
        "--password",
        "testpass",
        "--url",
        "https://test.url.ac.uk/dir/file.nc",
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    file_request = requests_mock.request_history[0]
    assert file_request.headers["Authorization"] == "Basic dGVzdHVzZXI6dGVzdHBhc3M="


def test_failed_auth_login(capsys, mock_token, requests_mock, tmp_path):
    mock_token(401)
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    file_url = "https://test.url.ac.uk/dir/file.nc"
    requests_mock.get(file_url, content=b"fake netcdf data", status_code=200)

    test_args = [
        "main.py",
        "--username",
        "testuser",
        "--password",
        "testpass",
        "--url",
        file_url,
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "authentication failed: invalid credentials" in captured.out


def test_ftp_login(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/file.nc"

    test_args = [
        "main.py",
        "--username",
        "anonymous",
        "--password",
        "user@email.com",
        "--url",
        url,
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        exit_code = main()

    assert exit_code is None
