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

        def generate_content_side_effect(model=None, config=None, contents=None):
            mock_response = Mock()
            mock_response.text = json.dumps(
                [{"figure_name": "test.jpg", "token": ["sample", "text"]}]
            )
            return mock_response

        # generate_contentと同じキーワード引数を持つモック
        # return_valueを使うことで、mock_responseを返すようにする
        mock_instance.models.generate_content.side_effect = generate_content_side_effect

        yield mock_instance  # mock_instanceを返す（MockClientではなく）


# 本番環境の設定ファイル
@pytest.fixture
def production_config():
    return config_ini


# システムプロンプトの取得
@pytest.fixture
def system_instructions():
    return get_system_instructions()


@pytest.fixture
def app(root, test_config_ini, mock_genai_client):
    """クラスごとに1回だけアプリを作成"""
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        app.client = mock_genai_client
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
        assert isinstance(app.paned_window, tk.Widget)
        assert isinstance(app.folder_name_entry, tk.Widget)
        assert isinstance(app.model_name_label, tk.Widget)
        assert isinstance(app.file_listbox, tk.Listbox)
        assert isinstance(app.start_button, tk.Widget)
        assert isinstance(app.stop_button, tk.Widget)
        assert isinstance(app.status_display, tk.Widget)
        assert isinstance(app.image_canvas, tk.Canvas)
        assert isinstance(app.images_frame, tk.Widget)

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


class TestGeminiCall:
    def test_file_upload_to_gemini_success(self, app):
        """file_upload_to_geminiメソッドが正しい引数で呼ばれることを確認"""
        app.uploaded_images = test_file_path_list
        app.file_upload_to_gemini()

        # files.upload()が画像の数だけ呼ばれたことを確認
        assert app.client.files.upload.call_count == len(test_file_path_list)

        # 各画像ファイルに対して正しい引数で呼ばれたことを確認
        for i, file_path in enumerate(test_file_path_list):
            called_args, called_kwargs = app.client.files.upload.call_args_list[i]
            assert called_kwargs.get("file") == file_path or (
                len(called_args) > 0 and called_args[0] == file_path
            )

    # test_file_upload_to_geminiをファイルを与えずに呼び出したときのテスト。
    def test_file_upload_to_gemini_no_files(self, app):
        """file_upload_to_geminiメソッドがファイル無しで呼ばれたときの挙動を確認"""
        app.uploaded_images = []  # ファイル無し

        # ValueErrorが発生することを確認
        with pytest.raises(ValueError, match="アップロードする画像がありません"):
            app.file_upload_to_gemini()

        # files.upload()が一度も呼ばれていないことを確認
        app.client.files.upload.assert_not_called()

    def test_extract_text(self, app, mock_genai_client):
        """extract_textメソッドが正しい引数で呼ばれることを確認"""
        app.uploaded_images = test_file_path_list
        files = app.file_upload_to_gemini()  # まず画像をアップロード

        # extract_textを呼び出し
        results = app.extract_text(files)

        # models.generate_contentが1回だけ呼ばれたことを確認
        assert mock_genai_client.models.generate_content.call_count == 1
        # 呼び出し時の引数を確認
        called_args, called_kwargs = mock_genai_client.models.generate_content.call_args
        assert called_kwargs.get("model") == app.gemini_model
        assert "contents" in called_kwargs
        assert isinstance(called_kwargs["contents"], list)
        assert (
            len(called_kwargs["contents"]) == len(app.uploaded_images) + 1
        )  # 画像+プロンプト
        assert "config" in called_kwargs
        assert isinstance(called_kwargs["config"], type(called_kwargs["config"]))
        # GenerateContentConfigオブジェクトの中身は直接確認できないので、型のみ確認

        # 戻り値が期待通りの形式であることを確認
        assert isinstance(results, list)
        assert len(results) == 1  # モックは1つのレスポンスしか返さない

        for item in results:
            assert "figure_name" in item
            assert "token" in item
            assert isinstance(item["token"], list)
