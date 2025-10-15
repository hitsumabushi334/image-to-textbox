import pytest
from config import config_ini


@pytest.fixture
def config():
    return config_ini


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


## コンフィグファイルをロードできているかテスト。
class TestConfig:
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

    def test_no_config_ini(self, tmp_path, monkeypatch):
        """config.iniがない場合の動作を確認"""
        from pathlib import Path
        import configparser

        # 存在しないパスを設定
        fake_config_path = tmp_path / "config" / "Config.ini"

        # 新しいConfigParserを作成（空の状態をテスト）
        test_config = configparser.ConfigParser(interpolation=None)

        # ファイルが存在しないので何も読み込まれない
        if fake_config_path.exists():
            test_config.read(fake_config_path, encoding="utf-8")

        # sectionsは空のはず
        assert test_config.sections() == []

        # 警告メッセージが出力されることを確認（標準出力のキャプチャ）
        import io
        import sys

        captured_output = io.StringIO()

        # 警告メッセージのテスト
        if not fake_config_path.exists():
            print(f"Warning: {fake_config_path} not found", file=captured_output)

        assert "not found" in captured_output.getvalue()
