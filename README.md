# Image to Textbox

画像（図・グラフ・表・実験写真など）から数値・文字を抽出し、構造化された JSON データとして出力する GUI アプリケーションです。

## 特徴

- 複数の画像ファイルを一括アップロード・処理
- Google Gemini API を使用したテキスト抽出
- 画像プレビュー機能（2 列レイアウト）
- 並列アップロード処理（最大 10 スレッド）
- カスタマイズ可能なシステムプロンプト

## 必要要件

- Python 3.12 以上
- Google Gemini API キー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd image-to-textbox
```

### 2. 依存パッケージのインストール

```bash
# uv を使用する場合（推奨）
uv sync

# または pip を使用する場合
pip install -e .

# 開発環境用パッケージも含める場合
pip install -e ".[dev]"
```

### 3. 設定ファイルの作成

`config.ini.example` をコピーして `config.ini` を作成し、API キーを設定します：

```bash
# Windows (PowerShell)
Copy-Item config\config.ini.example config\config.ini

# Linux/Mac
cp config/config.ini.example config/config.ini
```

`config/config.ini` を編集して API キーを設定：

```ini
[GEMINI]
api_key = YOUR_ACTUAL_API_KEY_HERE
model = gemini-2.5-pro

[GUI_SETTINGS]
window_size = 1170x450
icon_name = image-to-textbox.ico

[LOGGING]
log-level = INFO
encoding = utf-8
log_file = app.log
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 4. アプリケーションの起動

```bash
python main.py
```

## 使用方法

1. **ファイルのアップロード**

   - 「ファイルをアップロード」ボタンをクリック
   - JPEG/PNG 形式の画像ファイルを選択
   - 複数ファイルの同時選択が可能

2. **画像の確認**

   - 右側のパネルでアップロードした画像をプレビュー
   - 2 列レイアウトで表示

3. **処理の実行**

   - 「開始」ボタンをクリックして処理を開始
   - ステータス表示で進捗を確認

4. **リセット**
   - 「リセット」ボタンですべての画像をクリア

## テストの実行

### 通常のテスト実行

```bash
pytest tests/
```

### カバレッジ付きでテスト実行

```bash
pytest --cov=. --cov-report=html tests/
```

### CI 環境（ヘッドレス環境）でのテスト実行

#### 方法 1: pytest-xvfb を使用

```bash
# pytest-xvfbのインストール
pip install pytest-xvfb

# テスト実行
pytest --xvfb tests/
```

#### 方法 2: xvfb を手動で起動

```bash
# Linux環境の場合
sudo apt-get install xvfb
xvfb-run -a pytest tests/
```

#### 方法 3: 仮想ディスプレイを使用

```bash
pip install pyvirtualdisplay

# テスト実行前に環境変数を設定
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
pytest tests/
```

### テストのスキップ

特定のテストをスキップする場合：

```bash
# GUIテストをスキップ
pytest tests/ -m "not gui"

# 特定のテストクラスのみ実行
pytest tests/test_main.py::TestGeminiCall
```

## プロジェクト構成

```
.
├── config/
│   ├── config.ini              # 設定ファイル（要作成）
│   ├── config.ini.example      # 設定ファイルのサンプル
│   └── system_instruction.md   # システムプロンプト
├── tests/
│   ├── test_config.py          # 設定ファイルのテスト
│   ├── test_get_prompt.py      # プロンプト取得のテスト
│   └── test_main.py            # メインアプリケーションのテスト
├── config.py                   # 設定読み込み
├── get_prompt.py               # システムプロンプト取得
├── main.py                     # メインアプリケーション
├── pyproject.toml              # プロジェクト設定
└── README.md                   # このファイル
```

## ログ設定

ログは `config.ini` の `[LOGGING]` セクションで設定できます：

- `log-level`: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `log_file`: ログファイルのパス
- `encoding`: ログファイルのエンコーディング
- `format`: ログのフォーマット

ログは標準出力とファイルの両方に出力されます。

## トラブルシューティング

### API キーが無効

```
ValueError: GEMINI APIキーが設定されていません。
```

- `config/config.ini` で API キーが正しく設定されているか確認してください

### 画像のアップロードに失敗

- サポートされている画像形式（JPEG/PNG）を使用しているか確認
- ファイルパスに日本語などの特殊文字が含まれていないか確認

### テストが失敗する（TclError: no display name）

- ヘッドレス環境では `pytest --xvfb` または `xvfb-run -a pytest` を使用してください
- 詳細は「テストの実行」セクションを参照

## ライセンス

このプロジェクトのライセンスについては、プロジェクトの管理者にお問い合わせください。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まず issue を開いて変更内容を議論してください。

## サポート

問題が発生した場合は、GitHub の issue で報告してください。
