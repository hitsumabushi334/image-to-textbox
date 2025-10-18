import pytest
from configparser import ConfigParser
from pathlib import Path


@pytest.fixture
def config_params():
    return {
        "GEMINI": {
            "api_key": "YOUR_API_KEY_HERE",
            "model": "gemini-2.5-pro",
        },
        "GUI_SETTINGS": {
            "window_size": "1170x450",
            "icon_name": "image-to-textbox.ico",
        },
        "LOGGING": {
            "log_file": "app.log",
            "log-level": "INFO",
            "encoding": "utf-8",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def temp_config_file(tmp_path, config_params):
    """一時的なconfig.iniファイルを作成"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.ini"

    # ConfigParserで設定を書き込む
    cfg = ConfigParser()
    for section, options in config_params.items():
        cfg.add_section(section)
        for key, value in options.items():
            cfg.set(section, key, value)

    with open(config_file, "w", encoding="utf-8") as f:
        cfg.write(f)

    return config_file


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_load_config_with_valid_file(self, temp_config_file, config_params):
        """有効な設定ファイルが正しく読み込まれることを確認"""
        from config import load_config

        config = load_config(temp_config_file)

        # セクションの存在確認
        assert "GEMINI" in config
        assert "GUI_SETTINGS" in config
        assert "LOGGING" in config

        # 値の確認
        assert config["GEMINI"]["api_key"] == config_params["GEMINI"]["api_key"]
        assert config["GEMINI"]["model"] == config_params["GEMINI"]["model"]

    def test_load_config_with_nonexistent_file(self, tmp_path, capsys):
        """存在しない設定ファイルを指定した場合の動作を確認"""
        from config import load_config

        nonexistent_path = tmp_path / "nonexistent" / "config.ini"
        config = load_config(nonexistent_path)

        # 警告メッセージが出力されていることを確認
        captured = capsys.readouterr()
        assert f"Warning: {nonexistent_path} not found" in captured.out

        # 空の設定が返されることを確認
        assert config.sections() == []

    def test_load_config_with_default_path(self, monkeypatch, tmp_path, capsys):
        """デフォルトパスで読み込む場合のテスト"""
        from config import load_config

        # 存在しないデフォルトパスを設定
        fake_base = tmp_path / "nonexistent"
        monkeypatch.setattr("config.BASE", fake_base)

        config = load_config()

        captured = capsys.readouterr()
        expected_path = fake_base / "config" / "config.ini"
        assert f"Warning: {expected_path} not found" in captured.out

    def test_load_config_returns_configparser_instance(self, temp_config_file):
        """load_config()がConfigParserインスタンスを返すことを確認"""
        from config import load_config

        config = load_config(temp_config_file)

        assert isinstance(config, ConfigParser)

    def test_load_config_with_interpolation_none(self, tmp_path):
        """interpolation=Noneが設定されていることを確認"""
        from config import load_config

        # %記号を含む設定ファイルを作成
        config_file = tmp_path / "test_config.ini"
        config_file.write_text(
            "[TEST]\nvalue = %(asctime)s - %(name)s\n", encoding="utf-8"
        )

        config = load_config(config_file)

        # interpolationがNoneの場合、%記号がそのまま読み込まれる
        assert config["TEST"]["value"] == "%(asctime)s - %(name)s"


## コンフィグファイルをロードできているかテスト。
class TestConfig:
    """実際のconfig.iniファイルの内容をテスト"""

    @pytest.fixture
    def config(self):
        """実際のconfig.iniを読み込む"""
        from config import config_ini

        return config_ini

    def test_gemini_section(self, config, config_params):
        assert "GEMINI" in config
        assert "api_key" in config["GEMINI"]
        assert config["GEMINI"]["api_key"] == config_params["GEMINI"]["api_key"]
        assert "model" in config["GEMINI"]
        assert config["GEMINI"]["model"] == config_params["GEMINI"]["model"]

    def test_gui_settings_section(self, config, config_params):
        assert "GUI_SETTINGS" in config
        assert "window_size" in config["GUI_SETTINGS"]
        assert (
            config["GUI_SETTINGS"]["window_size"]
            == config_params["GUI_SETTINGS"]["window_size"]
        )
        assert "icon_name" in config["GUI_SETTINGS"]
        assert (
            config["GUI_SETTINGS"]["icon_name"]
            == config_params["GUI_SETTINGS"]["icon_name"]
        )

    def test_logging_section(self, config, config_params):
        assert "LOGGING" in config
        assert "log_file" in config["LOGGING"]
        assert config["LOGGING"]["log_file"] == config_params["LOGGING"]["log_file"]
        assert "log-level" in config["LOGGING"]
        assert config["LOGGING"]["log-level"] == config_params["LOGGING"]["log-level"]
        assert "encoding" in config["LOGGING"]
        assert config["LOGGING"]["encoding"] == config_params["LOGGING"]["encoding"]
        assert "format" in config["LOGGING"]
        assert config["LOGGING"]["format"] == config_params["LOGGING"]["format"]

    def test_no_extra_sections(self, config, config_params):
        assert len(config.sections()) == len(config_params)
        assert len(config["GEMINI"]) == len(config_params["GEMINI"])
        assert len(config["GUI_SETTINGS"]) == len(config_params["GUI_SETTINGS"])
        assert len(config["LOGGING"]) == len(config_params["LOGGING"])
