from pathlib import Path

from core import config_path, data_dir, platform_data_dir


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


def test_the_user_config_wins_over_the_platform_directory(tmp_path):
    archive = tmp_path / "archive"
    user = tmp_path / "user.env"
    user.write_text("LAWLIBRARY_DATA=%s\n" % archive.as_posix(), encoding="utf-8")
    assert data_dir({}, tmp_path / "missing.env", user) == archive.resolve()


def test_the_checkouts_dotenv_and_the_environment_win_over_the_user_config(tmp_path):
    user = tmp_path / "user.env"
    user.write_text("LAWLIBRARY_DATA=%s\n" % (tmp_path / "user").as_posix(), encoding="utf-8")
    dotenv = tmp_path / ".env"
    dotenv.write_text("LAWLIBRARY_DATA=%s\n" % (tmp_path / "checkout").as_posix(), encoding="utf-8")
    assert data_dir({}, dotenv, user) == (tmp_path / "checkout").resolve()
    assert data_dir({"LAWLIBRARY_DATA": str(tmp_path / "env")}, dotenv, user) == (tmp_path / "env").resolve()


def test_the_process_environment_finds_the_user_config_by_its_variable(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    user = tmp_path / "named.env"
    user.write_text('export LAWLIBRARY_DATA="%s"\n' % archive.as_posix(), encoding="utf-8")
    monkeypatch.delenv("LAWLIBRARY_DATA", raising=False)
    monkeypatch.delenv("MOUNT_DIRECTORY", raising=False)
    monkeypatch.setenv("LAWLIBRARY_CONFIG", str(user))
    found = data_dir(dotenv_path=tmp_path / "missing.env")
    assert found == archive.resolve()


def test_the_default_user_config_is_in_the_home_folder_not_appdata():
    found = config_path({})
    assert found == Path.home() / ".lawlibrary" / ".env"
    assert "AppData" not in found.parts


def test_an_explicit_environment_does_not_read_the_real_user_config(tmp_path):
    # {} supplies every source, so a person's own ~/.lawlibrary/.env cannot change the answer
    assert data_dir({}, tmp_path / "missing.env") == platform_data_dir()
