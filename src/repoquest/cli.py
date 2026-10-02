from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .agent import ask_agent
from .scanner import build_missions, scan_repository
from .tools import RepositoryTools


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repoquest",
        description="Turn a code repository into a guided exploration map.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--read", metavar="FILE", help="Read one repository file")
    actions.add_argument("--search", metavar="QUERY", help="Search repository text")
    actions.add_argument("--ask", metavar="QUESTION", help="Ask the model about the repository")
    parser.add_argument("--model", help="Optional model name for --ask")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        repository = scan_repository(args.path)
        tools = RepositoryTools(args.path)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)

    if args.read:
        result = tools.read_file(args.read)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["content"])
        return

    if args.search:
        result = tools.search_code(args.search)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else _format_matches(result))
        return

    if args.ask:
        try:
            answer = asyncio.run(ask_agent(args.path, args.ask, model=args.model))
        except (RuntimeError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            raise SystemExit(2)
        print(answer)
        return

    missions = build_missions(repository)
    if args.json:
        print(json.dumps({"repository": repository.to_dict(), "missions": missions}, ensure_ascii=False, indent=2))
        return

    print(f"RepoQuest map: {repository.root}")
    print(f"Files scanned: {repository.file_count}")
    print("Languages:")
    for language, count in repository.languages.items():
        print(f"  - {language}: {count}")

    print("\nImportant files:")
    for name in repository.important_files[:15]:
        print(f"  - {name}")

    print("\nMissions:")
    for index, mission in enumerate(missions, start=1):
        print(f"  {index}. {mission['title']}")
        print(f"     {mission['question']}")
        print(f"     Evidence: {mission['evidence']}")


def _format_matches(matches: list[dict]) -> str:
    if not matches:
        return "No matches found."
    return "\n".join(f"{item['path']}:{item['line']}: {item['text']}" for item in matches)


if __name__ == "__main__":
    main()
