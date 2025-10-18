# システムプロンプトを取得する関数
from os import path


def get_system_instructions():
    instruction_path = path.join("config", "system_instruction.md")
    if not path.exists(instruction_path):
        raise FileNotFoundError(
            f"System instruction file not found: {instruction_path}"
        )

    with open(instruction_path, encoding="utf-8") as f:
        system_instructions = f.read()
    return system_instructions


if __name__ == "__main__":
    print(get_system_instructions())
