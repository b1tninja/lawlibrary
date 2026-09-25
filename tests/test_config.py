from core import data_dir, platform_data_dir


def test_environment_wins_over_dotenv(tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text("LAWLIBRARY_DATA=/from-file\n", encoding="utf-8")
    found = data_dir({"LAWLIBRARY_DATA": str(tmp_path / "from-env")}, dotenv)
    assert found == (tmp_path / "from-env").resolve()


def test_dotenv_wins_over_the_platform_directory(tmp_path):
    archive = tmp_path / "archive"
    dotenv = tmp_path / ".env"
    dotenv.write_text("LAWLIBRARY_DATA=%s\n" % archive, encoding="utf-8")
    assert data_dir({}, dotenv) == archive.resolve()


def test_platform_directory_is_named_lawlibrary():
    assert platform_data_dir().name == "lawlibrary"
