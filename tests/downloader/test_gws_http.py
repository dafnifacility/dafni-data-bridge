import subprocess


def test_file_download(file_gws_url, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    result = subprocess.run(
        [
            "dataset-download-tool",
            "-n",
            "--url",
            file_gws_url.url_for("/dir/file.nc"),
            "--dest",
            str(dest_dir),
            "--checksum",
        ],
        capture_output=True,
        text=True,
    )

    file_gws_url.check_assertions()
    assert result.returncode == 0
    assert f"success: {dest_dir}/file.nc" in result.stdout


def test_directory_download(directory_gws_url, file_gws_url, file_gws_url_2, tmp_path):
    dest_dir = tmp_path / "data"
    dest_dir.mkdir()

    result = subprocess.run(
        [
            "dataset-download-tool",
            "-n",
            "--url",
            directory_gws_url.url_for("/dir/"),
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
