import subprocess


def test_token_auth(file_url, auth_url, tmp_path, monkeypatch):
    server = auth_url(200)
    file = file_url(200)

    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    monkeypatch.setenv("TOKEN_CREATE_URL", server.url_for("/api/token/create/"))

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--token",
            "mock-token-abc",
            "--url",
            file.url_for("/dir/file.nc"),
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    server.check_assertions()


def test_login_url(file_url, auth_url, tmp_path, monkeypatch):
    file = file_url(200)
    server = auth_url(200)

    monkeypatch.setenv("TOKEN_CREATE_URL", server.url_for("/api/token/create/"))

    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--username",
            "testuser",
            "--password",
            "testpass",
            "--url",
            file.url_for("/dir/file.nc"),
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file.check_assertions()
    assert f"success: {dest_dir}/file.nc" in result.stdout
    assert result.returncode == 0
