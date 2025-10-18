import configparser
from pathlib import Path

BASE = Path(__file__).resolve().parent  # この.pyがある場所
cfg_path = BASE / "config" / "config.ini"  # 例: 1つ上のconfig/config.ini
config_ini = configparser.ConfigParser(interpolation=None)

if cfg_path.exists():
    config_ini.read(cfg_path, encoding="utf-8")
else:
    # config.iniが存在しない場合の処理
    print(f"Warning: {cfg_path} not found")

if __name__ == "__main__":
    print(config_ini.sections())
