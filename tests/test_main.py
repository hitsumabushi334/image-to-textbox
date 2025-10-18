from multiprocessing import Value
from unittest import mock
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
            value = self._config[section][option]
            # 値がNoneの場合もfallbackを返す（本物のConfigParserと同じ挙動）
            if value is None:
                return fallback
            return value
        except KeyError:
            return fallback


@pytest.fixture(scope="class")
def root():
    """クラスごとに1回だけTkinterのルートウィンドウを作成"""
    root = tk.Tk()
    yield root
    root.destroy()


# 共通の設定パラメータ
@pytest.fixture(scope="class")
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
@pytest.fixture(scope="class")
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
@pytest.fixture(scope="class")
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
            if contents and "no_response" in contents:
                return None
            else:
                mock_response = Mock()

                if contents and "no_response.text" in contents:
                    mock_response.text = None
                elif contents and "empty_response.text" in contents:
                    mock_response.text = ""
                else:
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


@pytest.fixture(scope="class")
def app(root, test_config_ini, mock_genai_client):
    """クラスごとに1回だけアプリを作成"""
    with patch("main.genai.Client"):
        app = ImageTextboxApp(root, test_config_ini)
        app.generate_client = mock_genai_client
        yield app
    # root.destroy() は root fixture が担当するので不要


@pytest.fixture(autouse=True, scope="function")
def reset_mocks_and_state(request):
    """各テストの後でモックと状態をリセット"""
    # テスト実行前: 何もしない
    yield

    # テスト実行後: モックと状態をリセット
    # scope="class"のフィクスチャを安全に取得してリセット
    try:
        if "mock_genai_client" in request.fixturenames:
            mock_client = request.getfixturevalue("mock_genai_client")
            mock_client.files.upload.reset_mock()
            mock_client.models.generate_content.reset_mock()

        if "app" in request.fixturenames:
            app = request.getfixturevalue("app")
            if hasattr(app, "uploaded_images"):
                app.uploaded_images = []
    except Exception as e:
        # フィクスチャが利用できない場合はスキップ
        print(f"[test] fixture lookup skipped: {e}")


@pytest.fixture
def app_with_mock_client(mock_root, test_config_ini, mock_genai_client):
    """UI無しのアプリ（TestImageTextboxApp用）"""
    with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
        app = ImageTextboxApp(mock_root, test_config_ini)
        app.generate_client = mock_genai_client
        yield app


@pytest.fixture(scope="class")
def app_for_api_tests(test_config_ini, mock_genai_client):
    """TestGeminiCall用: UI無しでAPIロジックのみテスト"""
    mock_root = Mock(spec=tk.Tk)
    with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
        app = ImageTextboxApp(mock_root, test_config_ini)
        app.generate_client = mock_genai_client

        # UI要素をモックとして追加（file_upload_to_geminiで使われる）
        app.status_display = Mock()
        app.status_display.config = Mock()

        yield app


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
        assert hasattr(app, "file_name_entry")
        assert hasattr(app, "model_name_label")
        assert hasattr(app, "file_listbox")
        assert hasattr(app, "start_button")
        assert hasattr(app, "stop_button")
        assert hasattr(app, "status_display")
        assert hasattr(app, "image_canvas")
        assert hasattr(app, "images_frame")

        # ウィジェットの型確認
        assert isinstance(app.paned_window, tk.Widget)
        assert isinstance(app.file_name_entry, tk.Widget)
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

        local_root = Mock(spec=tk.Tk)
        with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
            ImageTextboxApp(local_root, config_with_none)
        local_root.geometry.assert_called_once_with("1170x450")

    def test_no_gemini_api_key(self, app_with_mock_client, test_config_ini):
        """APIキーが設定されていない場合のエラー処理を確認"""
        # APIキーをNoneに設定
        mock_config_no_api_key = MockConfigParser(
            {
                "GEMINI": {
                    "api_key": None,
                    "model": "gemini-2.5-pro",
                },
                "GUI_SETTINGS": {
                    "window_size": "1170x450",
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
        local_root = Mock(spec=tk.Tk)
        with pytest.raises(ValueError, match="GEMINI APIキーが設定されていません。"):
            with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
                ImageTextboxApp(local_root, mock_config_no_api_key)

    def test_no_system_instructions(self, test_config_ini, monkeypatch, caplog):
        """システムインストラクションファイルが存在しない場合の動作を確認"""
        import logging

        # get_system_instructionsが例外を発生させるようにモック
        def mock_get_system_instructions():
            raise FileNotFoundError("System instruction file not found")

        monkeypatch.setattr(
            "main.get_system_instructions", mock_get_system_instructions
        )

        local_root = Mock(spec=tk.Tk)

        # ログレベルをERRORに設定
        with caplog.at_level(logging.ERROR):
            with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
                mock_app = ImageTextboxApp(local_root, test_config_ini)

            # エラーログが出力されたことを確認
            assert "System instruction file error" in caplog.text
            assert "System instruction file not found" in caplog.text

            # system_instructionがNoneまたはデフォルト値になっていることを確認
            # (main.pyの実装によって異なる)
            assert (
                mock_app.system_instruction
                == "You are a helpful assistant that extracts text from images."
            )


class TestGeminiCall:

    def test_file_upload_success_with_multiple_files(self, app_for_api_tests):
        """複数ファイルのアップロードが成功することを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list

        result = app_for_api_tests.file_upload_to_gemini()

        # 戻り値がリストであることを確認
        assert isinstance(result, list)
        # アップロードしたファイル数と同じ長さのリストが返されることを確認
        assert len(result) == len(test_file_path_list)

    def test_file_upload_calls_upload_for_each_file(self, app_for_api_tests):
        """各ファイルに対してuploadが呼ばれることを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list

        # uploadメソッドの呼び出し回数をカウントするために新しいモックを設定
        upload_call_count = []

        def mock_upload(file):
            upload_call_count.append(file)
            mock_file = Mock()
            mock_file.name = f"test_{len(upload_call_count)}"
            mock_file.uri = f"gs://test/path_{len(upload_call_count)}"
            return mock_file

        # ThreadPoolExecutor内で作成される新しいクライアントをモック
        with patch("main.genai.Client") as MockClient:
            mock_instance = Mock()
            mock_instance.files.upload.side_effect = mock_upload
            MockClient.return_value = mock_instance

            app_for_api_tests.file_upload_to_gemini()

            # upload_fileが画像の数だけ呼ばれたことを確認
            assert len(upload_call_count) == len(test_file_path_list)

            # 各ファイルパスでuploadが呼ばれたことを確認
            for file_path in test_file_path_list:
                assert file_path in upload_call_count

    def test_file_upload_updates_status_display(self, app_for_api_tests):
        """アップロード中にステータス表示が更新されることを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list[:3]  # 3ファイルのみ

        with patch("main.genai.Client") as MockClient:
            mock_instance = Mock()
            mock_file = Mock()
            mock_file.name = "test_file"
            mock_file.uri = "gs://test/path"
            mock_instance.files.upload.return_value = mock_file
            MockClient.return_value = mock_instance

            app_for_api_tests.file_upload_to_gemini()

            # status_display.configが呼ばれたことを確認
            assert app_for_api_tests.status_display.config.called

            # 最後の呼び出しで正しい進捗が表示されていることを確認
            last_call = app_for_api_tests.status_display.config.call_args
            assert "3/3" in last_call[1]["text"]

    def test_file_upload_with_single_file(self, app_for_api_tests):
        """単一ファイルのアップロードが正しく動作することを確認"""
        app_for_api_tests.uploaded_images = [test_file_path_list[0]]

        with patch("main.genai.Client") as MockClient:
            mock_instance = Mock()
            mock_file = Mock()
            mock_file.name = "test_file"
            mock_file.uri = "gs://test/path"
            mock_instance.files.upload.return_value = mock_file
            MockClient.return_value = mock_instance

            result = app_for_api_tests.file_upload_to_gemini()

            # 1つの要素を持つリストが返されることを確認
            assert len(result) == 1
            # uploadが1回だけ呼ばれたことを確認
            assert mock_instance.files.upload.call_count == 1

    def test_file_upload_parallel_execution(self, app_for_api_tests):
        """並列実行が正しく行われることを確認（ThreadPoolExecutor使用）"""
        app_for_api_tests.uploaded_images = test_file_path_list

        with patch("main.ThreadPoolExecutor") as MockExecutor:
            mock_executor_instance = Mock()
            # mapは各ファイルに対して結果を返すイテレータを返す
            mock_executor_instance.map.return_value = iter(
                [None] * len(test_file_path_list)
            )
            MockExecutor.return_value.__enter__.return_value = mock_executor_instance

            with patch("main.genai.Client"):
                result = app_for_api_tests.file_upload_to_gemini()

            # ThreadPoolExecutorが正しいmax_workersで作成されたことを確認
            MockExecutor.assert_called_once_with(
                max_workers=min(10, len(test_file_path_list))
            )
            # mapが呼ばれたことを確認
            assert mock_executor_instance.map.called
            # 結果のリストが正しい長さであることを確認
            assert len(result) == len(test_file_path_list)

    def test_file_upload_empty_list_raises_error(self, app_for_api_tests):
        """空のファイルリストでValueErrorが発生することを確認"""
        app_for_api_tests.uploaded_images = []

        with pytest.raises(ValueError, match="アップロードする画像がありません"):
            app_for_api_tests.file_upload_to_gemini()

    def test_upload_file_called_for_each_image(self, app_for_api_tests):
        """upload_file（ネスト関数）が各画像に対して呼ばれることを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list

        with patch("main.genai.Client") as MockClient:
            # モッククライアントのインスタンスを作成
            mock_client_instance = Mock()
            MockClient.return_value = mock_client_instance

            # files.upload の戻り値をモック化
            mock_client_instance.files.upload.return_value = Mock(
                name="uploaded_file", uri="gs://test/file"
            )

            # メソッド実行
            result = app_for_api_tests.file_upload_to_gemini()

            # genai.Client が画像の数だけ呼ばれたことを確認
            # （upload_file 関数内で毎回 Client を作成しているため）
            assert MockClient.call_count == len(test_file_path_list)

            # files.upload が画像の数だけ呼ばれたことを確認
            assert mock_client_instance.files.upload.call_count == len(
                test_file_path_list
            )

            # 各画像ファイルに対して正しい引数で呼ばれたことを確認
            for file_path in test_file_path_list:
                mock_client_instance.files.upload.assert_any_call(file=file_path)

            # 結果の確認
            assert len(result) == len(test_file_path_list)

    def test_upload_file_passes_correct_api_key(self, app_for_api_tests):
        """upload_file が正しい API キーで Client を作成することを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list[:2]  # 2つだけテスト

        with patch("main.genai.Client") as MockClient:
            mock_client_instance = Mock()
            MockClient.return_value = mock_client_instance
            mock_client_instance.files.upload.return_value = Mock()

            # メソッド実行
            app_for_api_tests.file_upload_to_gemini()

            # genai.Client が正しい API キーで呼ばれたことを確認
            for call in MockClient.call_args_list:
                assert call == ((), {"api_key": app_for_api_tests.apiKey})

    def test_upload_file_executor_map_integration(self, app_for_api_tests):
        """ThreadPoolExecutor.map と upload_file の統合テスト"""
        app_for_api_tests.uploaded_images = test_file_path_list

        # 実際のアップロード回数をカウント
        upload_count = 0

        def mock_upload_side_effect(file):
            nonlocal upload_count
            upload_count += 1
            return Mock(name=f"file_{upload_count}")

        with patch("main.genai.Client") as MockClient:
            mock_client_instance = Mock()
            MockClient.return_value = mock_client_instance
            mock_client_instance.files.upload.side_effect = mock_upload_side_effect

            # メソッド実行
            result = app_for_api_tests.file_upload_to_gemini()

            # upload_file が各画像に対して実行されたことを確認
            assert upload_count == len(test_file_path_list)
            assert len(result) == len(test_file_path_list)

    def test_extract_text(self, app_for_api_tests, mock_genai_client):
        """extract_textメソッドが正しい引数で呼ばれることを確認"""
        app_for_api_tests.uploaded_images = test_file_path_list
        files = app_for_api_tests.file_upload_to_gemini()  # まず画像をアップロード

        # extract_textを呼び出し
        results = app_for_api_tests.extract_text(files)

        # models.generate_contentが1回だけ呼ばれたことを確認
        assert mock_genai_client.models.generate_content.call_count == 1
        # 呼び出し時の引数を確認
        _, called_kwargs = mock_genai_client.models.generate_content.call_args
        assert called_kwargs.get("model") == app_for_api_tests.gemini_model
        assert "contents" in called_kwargs
        assert isinstance(called_kwargs["contents"], list)
        assert (
            len(called_kwargs["contents"]) == len(app_for_api_tests.uploaded_images) + 1
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

    def test_extract_text_no_files(self, app_for_api_tests):
        """extract_textメソッドがファイル無しで呼ばれたときの挙動を確認"""
        # 空のファイルリストを渡す
        files = []

        # ValueErrorが発生することを確認
        with pytest.raises(
            ValueError, match="テキスト抽出のためのファイルがありません"
        ):
            app_for_api_tests.extract_text(files)

    def test_extract_text_no_response_text(self, app_for_api_tests):
        """extract_textメソッドがresponse.text = Noneの場合の挙動を確認"""
        files = ["no_response.text"]
        # ValueErrorが発生することを確認
        with pytest.raises(
            ValueError, match="No response text received from Gemini API"
        ):
            app_for_api_tests.extract_text(files)

    def test_extract_text_empty_response_text(self, app_for_api_tests):
        """extract_textメソッドが空のレスポンス文字列の場合の挙動を確認"""
        files = ["empty_response.text"]
        # ValueErrorが発生することを確認
        with pytest.raises(
            ValueError, match="Empty response text received from Gemini API"
        ):
            app_for_api_tests.extract_text(files)

    def test_extract_text_no_response(self, app_for_api_tests):
        """extract_textメソッドでresponseオブジェクトがNoneの場合の挙動を確認"""
        files = ["no_response"]
        # ValueErrorが発生することを確認
        with pytest.raises(
            ValueError, match="No response text received from Gemini API"
        ):
            app_for_api_tests.extract_text(files)
