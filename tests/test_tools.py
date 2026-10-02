from pathlib import Path

from repoquest.tools import RepositoryTools


def test_read_file_cannot_escape_repository(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    tools = RepositoryTools(tmp_path)

    result = tools.read_file("main.py")

    assert result["content"] == "print('hello')"
    try:
        tools.read_file("../outside.txt")
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise AssertionError("read_file allowed a path outside the repository")


def test_search_code_returns_line_evidence(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")
    tools = RepositoryTools(tmp_path)

    result = tools.search_code("HELLO")

    assert result == [{"path": "main.py", "line": 2, "text": "return 'hello'"}]
