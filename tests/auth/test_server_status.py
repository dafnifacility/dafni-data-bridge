import subprocess


def test_server_access_failure(file_url, auth_url, tmp_path, monkeypatch):
    server = auth_url(503)
    file = file_url(503)

    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    monkeypatch.setenv("TOKEN_CREATE_URL", server.url_for("/api/token/create/"))

    result = subprocess.run(
        [
            "ceda-download-tool",
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

    assert result.returncode == 1
    assert result.stdout.__contains__("download failed: failed to download")
    server.check_assertions()
