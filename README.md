# RepoQuest

RepoQuest turns an unfamiliar code repository into a guided exploration game.

The first milestone is deliberately deterministic and does not require an API key:

- scan a repository safely;
- build a compact project map;
- generate exploration missions from the repository evidence.

The next milestone will add an Agent that can answer questions using these repository tools.

## Run

From this directory:

```powershell
python -m repoquest .
```

To inspect another repository:

```powershell
python -m repoquest C:\path\to\repository
```

To get machine-readable output:

```powershell
python -m repoquest . --json
```

Repository tools:

```powershell
python -m repoquest . --read README.md
python -m repoquest . --search "def "
```

To enable the model-driven Agent:

```powershell
pip install -e ".[agent]"
$env:DEEPSEEK_API_KEY = "your-deepseek-api-key"
python -m repoquest . --ask "给我一个关于项目入口的探索任务，不要直接告诉我答案"
```

RepoQuest uses DeepSeek by default through its OpenAI-compatible API endpoint
(`https://api.deepseek.com`). To use OpenAI instead, set
`$env:REPOQUEST_PROVIDER = "openai"` and configure `OPENAI_API_KEY`.

The Agent uses only two local function tools in this milestone: `read_repository_file`
and `search_repository`. It is intentionally a single Agent so the tool-calling loop
is easy to inspect before adding memory or multiple specialists.

## Learning milestones

1. Deterministic repository tools
2. Structured project evidence
3. Agent tool calling and an agent loop
4. Hints, answer validation, and session state
5. Evaluation cases and a small web UI
