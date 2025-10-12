# システムプロンプトを取得する関数
def get_system_instructions():
    with open("config/system_instruction.md", encoding="utf-8") as f:
        system_instructions = f.read()
    return system_instructions


if __name__ == "__main__":
    print(get_system_instructions())
