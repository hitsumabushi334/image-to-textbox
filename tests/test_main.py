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


@pytest.fixture
def mock_root():
    """tk.Tkのモック"""
    mock_root = Mock(spec=tk.Tk)
    return mock_root


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
    """クラスごとに1回だけアプリを作成"""
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        yield app
    # root.destroy() は root fixture が担当するので不要


@pytest.fixture
def app_with_mock_client(mock_root, test_config_ini, mock_genai_client):
    with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
        app = ImageTextboxApp(mock_root, test_config_ini)
        app.client = mock_genai_client
        yield app
    return app


test_file_path_list = [
    "tests/test_image1.jpg",
    "tests/test_image2.png",
    "tests/test_image3.gif",
    "tests/test_image4.bmp",
    "tests/test_image5.tiff",
]


# GUIインスタンスの初期化テスト
class TestImageTextboxApp:
    def test_app_ui(self, app):
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

    def test_app_initialize(self, app_with_mock_client, test_config_ini):
        """アプリケーションの初期化が正しく行われることを確認"""
        # 設定ファイルの内容が正しく読み込まれていることを確認
        assert app_with_mock_client.config_ini == test_config_ini
        assert app_with_mock_client.gemini_model == test_config_ini["GEMINI"]["model"]
        assert app_with_mock_client.uploaded_images == []
        assert (
            app_with_mock_client.system_instruction is not None
        )  # get_system_instructions()の結果

    def test_window_geometry_configuration(self, app_with_mock_client, test_config_ini):
        """root.geometry()が正しい引数で1回呼ばれることを確認"""

        # geometry()が1回だけ呼ばれたことを確認
        app_with_mock_client.root.geometry.assert_called_once()

        # 正しい引数で呼ばれたことを確認
        expected_size = test_config_ini["GUI_SETTINGS"]["window_size"]
        app_with_mock_client.root.geometry.assert_called_with(expected_size)

    def test_window_geometry_with_fallback(self, app_with_mock_client):
        """window_sizeがNoneの場合、デフォルト値が使用されることを確認"""
        # window_sizeがNoneの設定
        config_with_none = MockConfigParser(
            {
                "GEMINI": {
                    "api_key": "test_key",
                    "model": "gemini-2.5-pro",
                },
                "GUI_SETTINGS": {
                    "window_size": None,
                    "icon_name": "test.ico",
                },
                "LOGGING": {
                    "log_file": "app.log",
                    "log-level": "INFO",
                    "encoding": "utf-8",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            }
        )

        # デフォルト値"1170x450"で呼ばれたことを確認
        app_with_mock_client.root.geometry.assert_called_once_with("1170x450")


class test_gemini_call:
    def test_file_upload_to_gemini(self, app_with_mock_client, test_file_path_list):
        """file_upload_to_geminiメソッドが正しい引数で1回呼ばれることを確認"""
        for file_path in test_file_path_list:
            app_with_mock_client.file_upload_to_gemini(file_path)

            # files.upload()が1回だけ呼ばれたことを確認
            app_with_mock_client.gemini_client.files.upload.assert_called_once()

            # 正しい引数で呼ばれたことを確認
            called_args, called_kwargs = (
                app_with_mock_client.gemini_client.files.upload.call_args
            )
            assert called_args[0] == file_path

            # モックの呼び出し履歴をリセットして次のループへ
            app_with_mock_client.gemini_client.files.upload.reset_mock()
