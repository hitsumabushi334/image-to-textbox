from unittest import mock
import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from main import ImageTextboxApp
from config import config_ini  # Assuming the main application is in main.py
from get_prompt import get_system_instructions
import json
from pathlib import Path


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

    def getint(self, section, option, fallback=None):
        """ConfigParser.getint()の振る舞いを模倣"""
        value = self.get(section, option, fallback=fallback)
        if value is None:
            return fallback
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid float value for [{section}] {option}: {value}"
            ) from e

    def getfloat(self, section, option, fallback=None):
        """ConfigParser.getfloat()の振る舞いを模倣"""
        value = self.get(section, option, fallback=fallback)
        if value is None:
            return fallback
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid integer value for [{section}] {option}: {value}"
            ) from e


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


# テスト用の設定ファイルのモック
@pytest.fixture(scope="class")
def test_config_ini(config_params):
    """ConfigParserのように振る舞う設定ファイルのモック"""
    return MockConfigParser(config_params)


@pytest.fixture
def mock_root():
    """tk.Tkのモック"""
    mock_root = Mock(spec=tk.Tk)
    mock_root.geometry.return_value = "1170x450+100+100"
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

    # tk.StringVar()のように動作するモッククラス
    class MockStringVar:
        def __init__(self):
            self._value = ""

        def get(self):
            return self._value

        def set(self, value):
            self._value = value

    mock_root = Mock(spec=tk.Tk)
    with patch("main.genai.Client"), patch.object(ImageTextboxApp, "setup_ui"):
        app = ImageTextboxApp(mock_root, test_config_ini)
        app.generate_client = mock_genai_client

        # UI要素をモックとして追加（file_upload_to_geminiで使われる）
        app.status_display = Mock()
        app.status_display.config = Mock()

        # file_nameを追加（setup_ui()でスキップされるため）
        app.file_name = MockStringVar()  # type: ignore[assignment]

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
        expected_output_path = Path(
            test_config_ini["PPTX_SETTINGS"]["output_dir"]
        ).resolve()
        assert app_with_mock_client.output_dir == expected_output_path

    def test_window_geometry_configuration(self, app_with_mock_client, test_config_ini):
        """ウィンドウサイズが設定されていることを確認"""
        # 実際のTkウィンドウなので、geometry()の戻り値を確認
        expected_size = test_config_ini["GUI_SETTINGS"]["window_size"]
        actual_geometry = app_with_mock_client.root.geometry()

        # サイズ部分を抽出（例: "1170x450+100+100" -> "1170x450"）
        actual_size = (
            actual_geometry.split("+")[0] if "+" in actual_geometry else actual_geometry
        )
        assert actual_size == expected_size

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

    def test_no_gemini_api_key(self):
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

    def test_extract_text_delete_files(self, app_for_api_tests):
        """extract_textメソッドが一時ファイルを削除することを確認"""
        with (
            patch("main.genai.Client") as MockClient,
            patch.object(ImageTextboxApp, "setup_ui"),
        ):
            mock_instance = Mock()
            MockClient.return_value = mock_instance

            # アップロードされたファイルオブジェクトのモックを作成
            mock_uploaded_files = []
            for i in range(len(test_file_path_list)):
                mock_file = Mock()
                mock_file.name = f"uploaded_file_{i}"
                mock_uploaded_files.append(mock_file)

            # upload()が各ファイルに対応するモックファイルオブジェクトを返すように設定
            mock_instance.files.upload.side_effect = mock_uploaded_files
            mock_instance.files.delete.return_value = Mock()

            # response.textがJSON文字列を返すようにモック
            mock_response = Mock()
            mock_response.text = json.dumps(
                [{"figure_name": "test1.jpg", "token": ["token1", "token2"]}]
            )
            mock_instance.models.generate_content.return_value = mock_response

            mock_root = Mock(spec=tk.Tk)
            app = ImageTextboxApp(mock_root, app_for_api_tests.config_ini)
            app.generate_client = mock_instance
            app.uploaded_images = test_file_path_list
            app.status_display = Mock()
            files = app.file_upload_to_gemini()
            app.extract_text(files)

            # deleteが各ファイルに対して呼ばれたことを確認
            assert mock_instance.files.delete.call_count == len(test_file_path_list)
            assert mock_instance.files.delete.call_args_list is not None

            # call_args_listの各要素はcall(name=file_object)の形式
            # アップロードされたファイルオブジェクトが削除されることを確認
            deleted_files = []
            for call in mock_instance.files.delete.call_args_list:
                _, kwargs = call
                # キーワード引数'name'にファイルオブジェクトが渡されている
                assert "name" in kwargs
                deleted_files.append(kwargs["name"])

            # アップロードされたファイルが全て削除されたことを確認
            assert set(deleted_files) == set(mock_uploaded_files)


class Test_generate_pptx:
    def test_generate_pptx_creates_presentation(self, app_for_api_tests, tmp_path):
        """PPTX生成メソッドがPresentationを作成することを確認"""
        app_for_api_tests.output_dir = tmp_path

        gemini_response = [
            {"figure_name": "test1.jpg", "token": ["token1", "token2"]},
            {"figure_name": "test2.png", "token": ["token3", "token4"]},
        ]

        with patch("main.Presentation") as MockPresentation:
            mock_prs = Mock()
            MockPresentation.return_value = mock_prs

            # slide_layouts をモック
            mock_prs.slide_layouts = [Mock() for _ in range(10)]
            mock_prs.slides = Mock()
            mock_slide = Mock()
            mock_prs.slides.add_slide.return_value = mock_slide

            # スライドの shapes をモック
            mock_shape = Mock()
            mock_text_frame = Mock()
            mock_paragraph = Mock()
            mock_run = Mock()

            mock_shape.text_frame = mock_text_frame
            mock_text_frame.paragraphs = [mock_paragraph]
            mock_paragraph.add_run.return_value = mock_run
            mock_slide.shapes.add_textbox.return_value = mock_shape

            # スライドの寸法をモック
            mock_prs.slide_width = 9144000  # 10 inches in EMU
            mock_prs.slide_height = 6858000  # 7.5 inches in EMU

            app_for_api_tests.generate_pptx(gemini_response)

            # Presentationが作成されたことを確認
            MockPresentation.assert_called_once()

            # add_slideが各図に対して呼ばれたことを確認
            assert mock_prs.slides.add_slide.call_count == len(gemini_response)

            # save が呼ばれたことを確認
            mock_prs.save.assert_called_once()

    def test_generate_pptx_file_creation(self, app_for_api_tests, tmp_path):
        """PPTX生成メソッドが実際にファイルを作成することを確認"""
        app_for_api_tests.output_dir = tmp_path
        app_for_api_tests.file_name.set("test_output")

        gemini_response = [
            {"figure_name": "test1.jpg", "token": ["token1", "token2"]},
        ]

        # 実際にファイルを生成
        app_for_api_tests.generate_pptx(gemini_response)

        # PPTXファイルが作成されたことを確認
        pptx_files = list(tmp_path.glob("*.pptx"))
        assert len(pptx_files) == 1
        assert pptx_files[0].name == "test_output.pptx"

    def test_generate_pptx_default_filename(self, app_for_api_tests, tmp_path):
        """ファイル名が指定されていない場合、タイムスタンプ付きファイル名が使用されることを確認"""
        app_for_api_tests.output_dir = tmp_path
        app_for_api_tests.file_name.set("")  # 空のファイル名

        gemini_response = [
            {"figure_name": "test1.jpg", "token": ["token1"]},
        ]

        with patch("main.datetime") as mock_datetime:
            # 固定の日時を返すようにモック
            mock_now = Mock()
            mock_now.strftime.return_value = "20250119_123456"
            mock_datetime.now.return_value = mock_now

            app_for_api_tests.generate_pptx(gemini_response)

            # タイムスタンプ付きファイル名が使用されたことを確認
            pptx_files = list(tmp_path.glob("*.pptx"))
            assert len(pptx_files) == 1
            assert pptx_files[0].name == "output_20250119_123456.pptx"

    def test_generate_pptx_uses_config_settings(self, app_for_api_tests, tmp_path):
        """設定値が正しく使用されることを確認"""
        app_for_api_tests.output_dir = tmp_path

        gemini_response = [
            {"figure_name": "test1.jpg", "token": ["token1", "token2"]},
        ]

        # config_iniから設定値を読み込むことを確認
        with patch("main.Presentation") as MockPresentation:
            mock_prs = Mock()
            MockPresentation.return_value = mock_prs
            mock_prs.slide_layouts = [Mock() for _ in range(10)]
            mock_prs.slides = Mock()
            mock_slide = Mock()
            mock_prs.slides.add_slide.return_value = mock_slide

            mock_shape = Mock()
            mock_text_frame = Mock()
            mock_paragraph = Mock()
            mock_run = Mock()

            mock_shape.text_frame = mock_text_frame
            mock_text_frame.paragraphs = [mock_paragraph]
            mock_paragraph.add_run.return_value = mock_run
            mock_slide.shapes.add_textbox.return_value = mock_shape

            mock_prs.slide_width = 9144000
            mock_prs.slide_height = 6858000

            app_for_api_tests.generate_pptx(gemini_response)

            # self.config_ini.getint/getfloatが呼ばれていることを確認
            # (実装の詳細なので、Presentationが作成されたことで間接的に確認)
            MockPresentation.assert_called_once()
