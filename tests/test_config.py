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
        "PPTX_SETTINGS": {
            "output_dir": "pptx_output",
            "font_name": "Arial",
            "font_size": "14",
            "char_width_in": "0.097",
            "min_w_in": "0.45",
            "min_h_in": "0.30",
            "wrap_padding_in": "0.20",
            "layout_num": "6",
            "margin_l": "0.4",
            "margin_r": "0.4",
            "margin_t": "0.5",
            "margin_b": "0.4",
            "heading_h": "0.4",
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
        with pytest.raises(FileNotFoundError):
            config = load_config(nonexistent_path)
            assert config.sections() == []

    def test_load_config_with_default_path(self, monkeypatch, tmp_path, capsys):
        """デフォルトパスで読み込む場合のテスト"""
        from config import load_config

        # 存在しないデフォルトパスを設定
        fake_base = tmp_path / "nonexistent"
        monkeypatch.setattr("config.BASE", fake_base)

        with pytest.raises(FileNotFoundError):
            load_config()

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
    @pytest.fixture
    def config(self):
        """実際のconfig.iniを読み込む(無ければskip)"""
        import pytest
        from config import config_ini, BASE

        cfg_path = BASE / "config" / "config.ini"
        if not cfg_path.exists():
            pytest.skip(f"missing real config file: {cfg_path}")
        return config_ini

    def test_gemini_section(self, config, config_params):
        section_name = "GEMINI"
        assert section_name in config

        expected_settings = config_params[section_name]
        actual_settings = config[section_name]

        for key, expected_value in expected_settings.items():
            assert key in actual_settings
            assert actual_settings[key] == expected_value

    def test_gui_settings_section(self, config, config_params):
        section_name = "GUI_SETTINGS"
        assert section_name in config

        expected_settings = config_params[section_name]
        actual_settings = config[section_name]

        for key, expected_value in expected_settings.items():
            assert key in actual_settings
            assert actual_settings[key] == expected_value

    def test_logging_section(self, config, config_params):
        section_name = "LOGGING"
        assert section_name in config

        expected_settings = config_params[section_name]
        actual_settings = config[section_name]

        for key, expected_value in expected_settings.items():
            assert key in actual_settings
            assert actual_settings[key] == expected_value

    def test_pptx_settings_section(self, config, config_params):
        section_name = "PPTX_SETTINGS"
        assert section_name in config

        expected_settings = config_params[section_name]
        actual_settings = config[section_name]

        for key, expected_value in expected_settings.items():
            assert key in actual_settings
            assert actual_settings[key] == expected_value

    def test_no_extra_sections(self, config, config_params):
        assert len(config.sections()) == len(config_params)
        assert len(config["GEMINI"]) == len(config_params["GEMINI"])
        assert len(config["GUI_SETTINGS"]) == len(config_params["GUI_SETTINGS"])
        assert len(config["LOGGING"]) == len(config_params["LOGGING"])
        assert len(config["PPTX_SETTINGS"]) == len(config_params["PPTX_SETTINGS"])
