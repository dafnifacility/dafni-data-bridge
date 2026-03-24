import subprocess


def test_file_access(file_url, tmp_path):
    file = file_url(200)

    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--token",
            "mock-token-ab",
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
    assert result.returncode == 0
    assert f"success: {dest_dir}/file.nc" in result.stdout


def test_file_access_failure(file_url, tmp_path):
    file = file_url(401)

    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    result = subprocess.run(
        [
            "dataset-download-tool",
            "--token",
            "mock-token-ab",
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
    assert result.returncode == 1
    assert "File not accesssible! Check login or file URL" in result.stdout


def test_local_download_ceda(file_url, auth_url, tmp_path, monkeypatch):
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

    file_path = dest_dir / "file.nc"

    assert f"success: {dest_dir}/file.nc" in result.stdout
    assert file_path.read_text() == "fake netcdf data"
    assert result.returncode == 0
    file.check_assertions()


def test_multiple_local_download_ceda(file_url, file_url_2, auth_url, tmp_path, monkeypatch):
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
            str(f"{file.url_for("/dir/file.nc")}| {file_url_2.url_for("/dir/file2.nc")}"),
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
    assert file_path.read_text() == "fake netcdf data"
    assert file_path_2.read_text() == "2nd fake netcdf data"
    file.check_assertions()


def test_directory_local_download(mock_ceda_directory, file_url, file_url_2, auth_url, tmp_path, monkeypatch):
    server = auth_url(200)
    file = file_url(200)

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
            mock_ceda_directory.url_for("/dir"),
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file_path = dest_dir / "dir/file.nc"
    file_path_2 = dest_dir / "dir/file2.nc"
    download_dir = dest_dir / "dir"

    assert result.returncode == 0
    assert len(list(download_dir.iterdir())) == 2
    assert file_path.read_text() == "fake netcdf data"
    assert file_path_2.read_text() == "2nd fake netcdf data"
    file.check_assertions()
