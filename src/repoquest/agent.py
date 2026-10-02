from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from .scanner import scan_repository
from .tools import RepositoryTools


def _configure_provider(model: str | None = None) -> str | None:
    """Configure the model provider used by the Agents SDK."""

    provider = os.getenv("REPOQUEST_PROVIDER", "deepseek").lower()
    requested_model = model or os.getenv("REPOQUEST_MODEL")

    if provider == "deepseek":
        try:
            from agents import set_default_openai_client, set_tracing_disabled
            from openai import AsyncOpenAI
        except ImportError as error:
            raise RuntimeError(
                "The Agent SDK is not installed. Run: pip install -e \".[agent]\""
            ) from error

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. Add your DeepSeek key in the current terminal."
            )

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        set_default_openai_client(client, use_for_tracing=False)
        set_tracing_disabled(True)
        return requested_model or "deepseek-flash"

    if provider == "openai":
        return requested_model

    raise RuntimeError(
        f"Unknown REPOQUEST_PROVIDER={provider!r}. Use 'deepseek' or 'openai'."
    )


def build_agent(root: str | Path, model: str | None = None):
    """Build the first RepoQuest agent and expose repository tools to it."""

    try:
        from agents import Agent, function_tool
    except ImportError as error:
        raise RuntimeError(
            "The Agent SDK is not installed. Run: pip install -e \".[agent]\""
        ) from error

    repository = scan_repository(root)
    repository_tools = RepositoryTools(root)
    map_json = json.dumps(repository.to_dict(), ensure_ascii=False, indent=2)
    resolved_model = _configure_provider(model)

    @function_tool
    def read_repository_file(path: str) -> str:
        """Read a UTF-8 text file inside the repository. Use a relative path."""

        return json.dumps(repository_tools.read_file(path), ensure_ascii=False)

    @function_tool
    def search_repository(query: str) -> str:
        """Search repository text and return matching paths, lines, and snippets."""

        return json.dumps(repository_tools.search_code(query), ensure_ascii=False)

    instructions = f"""
You are RepoQuest, a friendly codebase exploration guide.

Your goal is to help a learner understand this repository, not to write code for them.
Use the repository tools whenever you need evidence. Do not invent file names,
architecture, or behavior. When answering, cite evidence as `path:line` when a
line number is available, or cite the file path when it is not.

Start with a concise answer, then explain the reasoning. If the learner asks for
a challenge, create one question, give the relevant evidence path, and do not
reveal the answer unless they ask for a hint.

Repository map collected before this run:
{map_json}
""".strip()

    agent_kwargs = {
        "name": "RepoQuest Guide",
        "instructions": instructions,
        "tools": [read_repository_file, search_repository],
    }
    if resolved_model:
        agent_kwargs["model"] = resolved_model
    return Agent(**agent_kwargs)


async def ask_agent(root: str | Path, question: str, model: str | None = None) -> str:
    """Run one question through RepoQuest."""

    try:
        from agents import Runner
    except ImportError as error:
        raise RuntimeError(
            "The Agent SDK is not installed. Run: pip install -e \".[agent]\""
        ) from error

    agent = build_agent(root, model=model)
    result = await Runner.run(agent, question)
    return result.final_output


def ask_agent_sync(root: str | Path, question: str, model: str | None = None) -> str:
    return asyncio.run(ask_agent(root, question, model=model))
