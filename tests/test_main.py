import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
from config import config_ini  # Assuming the main application is in main.py
from get_prompt import get_system_instructions


@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()


# テスト用の設定ファイルのモック
@pytest.fixture
def test_config_ini(config: dict):
    api_key, model, window_size = config
    test_config_ini = Mock()
    test_config_ini["GEMINI"]["api_key"] = api_key
    test_config_ini["GEMINI"]["model"] = model
    test_config_ini["GUI_SETTINGS"]["window_size"] = window_size
    return test_config_ini


# 本番環境の設定ファイル
@pytest.fixture
def production_config():
    return config_ini


# システムプロンプトの取得
@pytest.fixture
def system_instructions():
    return get_system_instructions()


@pytest.fixture
def app(root, test_config_ini):
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        yield app
    return app
