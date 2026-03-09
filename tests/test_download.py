import sys
from unittest.mock import patch

import pytest

from ceda_download_tool.main import main


def test_local_download(mock_file, requests_mock, tmp_path):
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
    file_path = dest_dir / "file.nc"

    assert file_path.read_text() == "fake netcdf data"


def test_multiple_local_download(mock_file, mock_file_2, requests_mock, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    test_args = [
        "main.py",
        "--token",
        "mock-token-abc",
        "--url",
        "https://test.url.ac.uk/dir/file.nc, https://test.url.ac.uk/dir/file2.nc",
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    file_path = dest_dir / "file.nc"
    file_path_2 = dest_dir / "file2.nc"

    assert len(list(dest_dir.iterdir())) == 2
    assert file_path.read_text() == "fake netcdf data"
    assert file_path_2.read_text() == "2nd fake netcdf data"


def test_directory_local_download(mock_directory, mock_file, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    test_args = [
        "main.py",
        "--token",
        "mock-token-abc",
        "--url",
        "https://test.url.ac.uk/dir",
        "--dest",
        str(dest_dir),
        "--checksum",
    ]
    with patch.object(sys, "argv", test_args):
        main()

    file_path = dest_dir / "dir/file.nc"
    assert file_path.read_text() == "fake netcdf data"


def test_invalid_url(capsys, mock_file, requests_mock, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    test_args = [
        "main.py",
        "--token",
        "mock-token-abc",
        "--url",
        "url.com/file.nc",
        "--dest",
        str(dest_dir),
        "--checksum",
    ]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "url validation failed" in captured.out


def test_ftp_download(mock_ftp_server, tmp_path):
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
        main()

    file_path = dest_dir / "file.nc"
    assert file_path.read_text() == "mocked ftp file.nc"
