# me-ai-tools

Scripts and utilities that help AI agents validate, analyze, and fix code.

This repo complements [me-ai-coder](https://github.com/JakubKamarski/ai-coder) (rules, skills, specs). Rules describe *what* to check; this repo provides runnable checks that produce structured findings for agents to act on.

## Layout

| Directory | Purpose |
|-----------|---------|
| `code-validator/` | Java static analysis (`javal`) — task-scoped validation with AI-readable output |

More tool directories may be added over time (e.g. diff analyzers, dependency scanners).

## Usage

Install the global command once:

```bash
./projects/me-ai-tools/code-validator/install.sh
```

Then run from a repository checkout:

```bash
javal <TASK-ID> [repo-path]
javal PLOG-5164 --format task
```

If `javal` is not on `PATH`, install the tool — do not call the validator script directly.

See `code-validator/README.md` for full usage, task scope, and output formats.

## Workspace placement

Clone or keep this repo under your IDE workspace `projects/` folder alongside application repositories:

```
~/work/
├── projects/
│   ├── me-ai-coder/    # rules & skills
│   ├── me-ai-tools/    # this repo
│   └── locus-fc-orlen/ # application repos
└── tasks/
```
