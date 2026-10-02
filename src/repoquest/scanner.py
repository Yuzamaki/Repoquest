from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
}

IMPORTANT_FILES = {
    "README.md",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
}

ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "manage.py",
    "main.js",
    "index.js",
    "server.js",
    "main.ts",
    "index.ts",
    "main.go",
}


@dataclass(frozen=True)
class RepositoryMap:
    root: str
    file_count: int
    languages: dict[str, int]
    important_files: list[str]
    likely_entrypoints: list[str]
    directories: list[str]
    files: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def scan_repository(root: str | Path, max_files: int = 3000) -> RepositoryMap:
    """Collect small, explainable pieces of evidence about a repository."""

    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Repository does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root_path}")

    discovered_files: list[str] = []
    discovered_directories: set[str] = set()
    languages: Counter[str] = Counter()
    important_files: list[str] = []
    likely_entrypoints: list[str] = []

    for path in sorted(root_path.rglob("*")):
        relative = _relative(path, root_path)
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        if path.is_dir():
            if relative != ".":
                discovered_directories.add(relative)
            continue
        if len(discovered_files) >= max_files:
            break

        discovered_files.append(relative)
        suffix = path.suffix.lower()
        if suffix in LANGUAGE_BY_SUFFIX:
            languages[LANGUAGE_BY_SUFFIX[suffix]] += 1
        if path.name in IMPORTANT_FILES or path.name in ENTRYPOINT_NAMES:
            important_files.append(relative)
        if path.name in ENTRYPOINT_NAMES:
            likely_entrypoints.append(relative)

    return RepositoryMap(
        root=str(root_path),
        file_count=len(discovered_files),
        languages=dict(languages.most_common()),
        important_files=sorted(important_files),
        likely_entrypoints=sorted(likely_entrypoints),
        directories=sorted(discovered_directories),
        files=discovered_files,
    )


def build_missions(repo: RepositoryMap) -> list[dict[str, str]]:
    """Create evidence-backed starter missions without using a model yet."""

    missions = []
    entrypoint = repo.likely_entrypoints[0] if repo.likely_entrypoints else None
    readme = next((name for name in repo.important_files if name.endswith("README.md")), None)

    if entrypoint:
        missions.append(
            {
                "id": "entrypoint",
                "title": "Find the starting point",
                "question": f"What role does `{entrypoint}` play, and what happens first when the program starts?",
                "evidence": entrypoint,
            }
        )
    elif readme:
        missions.append(
            {
                "id": "entrypoint",
                "title": "Find the starting point",
                "question": f"According to `{readme}`, how is this project started or used?",
                "evidence": readme,
            }
        )

    if repo.languages:
        top_language = next(iter(repo.languages))
        missions.append(
            {
                "id": "architecture",
                "title": "Sketch the architecture",
                "question": f"Which directories appear to contain the main {top_language} implementation, and what responsibilities do they have?",
                "evidence": ", ".join(repo.directories[:5]) or "repository root",
            }
        )

    test_files = [
        name
        for name in repo.files
        if "test" in Path(name).name.lower() or "spec" in Path(name).name.lower()
    ]
    missions.append(
        {
            "id": "verification",
            "title": "Find the safety net",
            "question": "Where are the tests, checks, or examples that explain how this project is expected to behave?",
            "evidence": ", ".join(test_files[:5]) or "No obvious test file found",
        }
    )
    return missions
