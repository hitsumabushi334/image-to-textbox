import pytest
from get_prompt import get_system_instructions


@pytest.fixture
def prompt():
    with open("config/system_instruction.md", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def system_instructions():
    return get_system_instructions()


class TestGetPrompt:
    def test_system_instructions(self, system_instructions, prompt):
        assert system_instructions == prompt

    def test_file_not_found(self, monkeypatch):
        # 存在しないパスを指定してFileNotFoundErrorを確認
        monkeypatch.setattr(
            "os.path.exists", lambda x: False
        )  # 常にFalseを返すようにモンキーパッチ

        with pytest.raises(FileNotFoundError):
            get_system_instructions()
