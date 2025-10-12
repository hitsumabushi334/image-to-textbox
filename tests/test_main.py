from curses import window
from unittest import mock
from httpx import patch
import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
import configparser  # Assuming the main application is in main.py


@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()


# テスト用の設定ファイルのモック
@pytest.fixture
def test_config_ini(config: dict):
    api_key, model, window_size = config
    test_config_ini = mock.Mock()
    test_config_ini["GEMINI"]["api_key"] = api_key
    test_config_ini["GEMINI"]["model"] = model
    test_config_ini["GUI_SETTINGS"]["window_size"] = window_size
    return test_config_ini


@pytest.fixture
def app(root, test_config_ini):
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        yield app
    return app
