import subprocess


def test_ftp_login(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/dir/file.nc"

    result = subprocess.run(
        [
            "dataset-download-tool",
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

    assert result.returncode == 0
    assert f"success: {dest_dir}/file.nc" in result.stdout


def test_ftp_login_failed(mock_ftp_server, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    host, port = mock_ftp_server
    url = f"ftp://{host}:{port}/file.nc"

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--username",
            "wrongusername",
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

    assert result.returncode == 1
    assert "530 Authentication failed." in result.stdout
