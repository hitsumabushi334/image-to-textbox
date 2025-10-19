import configparser
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent  # この.pyがある場所


def load_config(config_path: Optional[Path] = None) -> configparser.ConfigParser:
    """
    設定ファイルを読み込む

    Args:
        config_path: 設定ファイルのパス。Noneの場合はデフォルトパスを使用

    Returns:
        ConfigParser: 読み込んだ設定
    """
    if config_path is None:
        config_path = BASE / "config" / "config.ini"

    config_ini = configparser.ConfigParser(interpolation=None)

    if config_path.exists():
        config_ini.read(config_path, encoding="utf-8")
    else:
        # config.iniが存在しない場合の処理
        raise FileNotFoundError(f"Warning: {config_path} not found")

    return config_ini


# モジュールレベルでの初期化（後方互換性のため）
try:
    config_ini = load_config()
except FileNotFoundError as e:
    print(e)
    config_ini = configparser.ConfigParser(interpolation=None)

if __name__ == "__main__":
    print(config_ini.sections())
