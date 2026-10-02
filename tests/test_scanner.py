from pathlib import Path

from repoquest.scanner import build_missions, scan_repository


def test_scan_repository_ignores_generated_directories(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    generated = tmp_path / "node_modules" / "package"
    generated.mkdir(parents=True)
    (generated / "index.js").write_text("ignored", encoding="utf-8")

    result = scan_repository(tmp_path)

    assert result.file_count == 2
    assert result.likely_entrypoints == ["main.py"]
    assert result.languages == {"Python": 1}


def test_missions_include_evidence() -> None:
    result = scan_repository(Path(__file__).parents[2])

    missions = build_missions(result)

    assert missions
    assert all(mission["evidence"] for mission in missions)
