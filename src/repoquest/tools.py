from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

from .scanner import IGNORED_DIRECTORIES


@dataclass(frozen=True)
class SearchMatch:
    path: str
    line: int
    text: str


class RepositoryTools:
    """Small, safe tools that an Agent can use to investigate a repository."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {self.root}")

    def _safe_path(self, relative_path: str | Path) -> Path:
        candidate = (self.root / Path(relative_path)).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as error:
            raise ValueError("Path must stay inside the repository") from error
        if not candidate.is_file():
            raise FileNotFoundError(f"File does not exist: {relative_path}")
        return candidate

    def read_file(self, relative_path: str | Path, max_chars: int = 12_000) -> dict:
        """Read a text file while keeping the returned context bounded."""

        path = self._safe_path(relative_path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"File is not UTF-8 text: {relative_path}") from error

        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]
        return {
            "path": path.relative_to(self.root).as_posix(),
            "content": content,
            "truncated": truncated,
        }

    def search_code(self, query: str, max_results: int = 20) -> list[dict]:
        """Search text files and return line-level evidence for the Agent."""

        query = query.strip().lower()
        if not query:
            raise ValueError("Search query cannot be empty")

        matches: list[SearchMatch] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or any(part in IGNORED_DIRECTORIES for part in path.parts):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(lines, start=1):
                if query in line.lower():
                    matches.append(
                        SearchMatch(
                            path=path.relative_to(self.root).as_posix(),
                            line=number,
                            text=line.strip(),
                        )
                    )
                    if len(matches) >= max_results:
                        return [asdict(match) for match in matches]
        return [asdict(match) for match in matches]
