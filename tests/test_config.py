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

    def test_no_extra_sections(self, config, config_params):
        assert len(config.sections()) == len(config_params)
        assert len(config["GEMINI"]) == len(config_params["GEMINI"])
        assert len(config["GUI_SETTINGS"]) == len(config_params["GUI_SETTINGS"])
