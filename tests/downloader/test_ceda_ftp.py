import subprocess


def test_ftp_download(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/dir/file.nc"

    result = subprocess.run(
        [
            "ceda-download-tool",
            "--username",
            "anonymous",
            "--password",
            "user@email.com",
            "--url",
            url,
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file_path = dest_dir / "file.nc"

    assert result.returncode == 0
    assert "mocked ftp file.nc" in file_path.read_text()


def test_ftp_dir_download(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/dir/"

    result = subprocess.run(
        [
            "ceda-download-tool",
            "--username",
            "anonymous",
            "--password",
            "user@email.com",
            "--url",
            url,
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file_path = dest_dir / "file.nc"
    file_path_2 = dest_dir / "file2.nc"

    assert result.returncode == 0
    assert len(list(dest_dir.iterdir())) == 2
    assert "mocked ftp file.nc" in file_path.read_text()
    assert "2nd mocked ftp file.nc" in file_path_2.read_text()


def test_ftp_download_failure(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/dir/nofile.nc"

    result = subprocess.run(
        [
            "ceda-download-tool",
            "--username",
            "anonymous",
            "--password",
            "user@email.com",
            "--url",
            url,
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file_path = dest_dir / "file.nc"

    assert result.returncode == 1
    assert not file_path.exists()
    assert "550 /dir/nofile.nc is not retrievable." in result.stdout
