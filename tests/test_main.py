from tkinter import ttk
import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
from config import config_ini  # Assuming the main application is in main.py
from get_prompt import get_system_instructions
import json


class MockConfigParser:
    """ConfigParserのような振る舞いをするモッククラス"""

    def __init__(self, config_dict):
        self._config = config_dict

    def __getitem__(self, key):
        """辞書のようにアクセス可能: config["GEMINI"]["api_key"]"""
        return self._config[key]

    def get(self, section, option, fallback=None):
        """ConfigParser.get()の振る舞いを模倣"""
        try:
            return self._config[section][option]
        except KeyError:
            return fallback


@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()


# 共通の設定パラメータ
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


# テスト用の設定ファイルのモック
@pytest.fixture
def test_config_ini(config_params):
    """ConfigParserのように振る舞う設定ファイルのモック"""
    return MockConfigParser(config_params)


# 目的: アプリのロジックをテスト（APIの動作は検証しない）
# 必要な振る舞い: メソッド呼び出しと戻り値のみ
# genai.Clientのモック
@pytest.fixture
def mock_genai_client():
    with patch("main.genai.Client") as MockClient:
        mock_instance = Mock()
        MockClient.return_value = mock_instance

        # 1. files.upload のモック（シンプル）
        mock_file = Mock()
        mock_file.name = "test_file"
        mock_file.uri = "gs://test/path"
        mock_instance.files.upload.return_value = mock_file

        # 2. models.generate_content のモック（シンプル）
        mock_response = Mock()
        mock_response.text = json.dumps(
            [{"figure_name": "test.jpg", "token": ["sample", "text"]}]
        )
        mock_instance.models.generate_content.return_value = mock_response

        yield MockClient


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


# GUIインスタンスの初期化テスト
class TestImageTextboxApp:
    def test_app_ui(self, app, test_config_ini):
        """アプリケーションの初期化が正しく行われることを確認"""
        assert app is not None
        assert app.root is not None

        # 主要なUI要素の存在確認
        assert hasattr(app, "paned_window")
        assert hasattr(app, "folder_name_entry")
        assert hasattr(app, "model_name_label")
        assert hasattr(app, "file_listbox")
        assert hasattr(app, "start_button")
        assert hasattr(app, "stop_button")
        assert hasattr(app, "status_display")
        assert hasattr(app, "image_canvas")
        assert hasattr(app, "images_frame")

        # ウィジェットの型確認
        assert isinstance(app.paned_window, ttk.PanedWindow)
        assert isinstance(app.folder_name_entry, ttk.Entry)
        assert isinstance(app.model_name_label, ttk.Label)
        assert isinstance(app.file_listbox, tk.Listbox)
        assert isinstance(app.start_button, ttk.Button)
        assert isinstance(app.stop_button, ttk.Button)
        assert isinstance(app.status_display, ttk.Label)
        assert isinstance(app.image_canvas, tk.Canvas)
        assert isinstance(app.images_frame, ttk.Frame)
