# javal — Java Validator

`javal` validates **only Java lines added or changed in task commits** on the current branch. It uses tree-sitter for parsing and applies discrete rules that emit findings for AI agents.

## Install

Same pattern as `luv` (`locus-update-version`):

```bash
./install.sh
```

Registers `javal` in `~/.local/bin` (macOS/Linux) or `~/bin` (Git Bash).

```bash
./uninstall.sh
```

`javal` must be on `PATH`. If unavailable, install the tool — agents must not call `validate.py` directly.

## Usage

```bash
javal <TASK-ID> [repo-path]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `TASK-ID` | yes | Task id used in commit messages (e.g. `PLOG-5164`) |
| `repo-path` | no | Repository to analyze. Defaults to the **current working directory** |

`repo-path` may be absolute or relative to the shell cwd.

### Examples

```bash
# Analyze current directory (e.g. inside a worktree checkout)
javal PLOG-5164

# Explicit current directory
javal PLOG-5164 .

# Relative path from workspace root
javal PLOG-5164 projects/locus-fc-orlen

# Worktree path
javal PLOG-5164 worktrees/PLOG-5164/locus-fc-orlen

# Task-file todo output
javal PLOG-5164 --format task

# Markdown report
javal PLOG-5164 --format markdown worktrees/PLOG-5164/locus-fc-orlen
```

## Task scope

`javal` inspects commits whose subject starts with:

```text
<TASK-ID> |
```

Examples that match `PLOG-5164`:

- `PLOG-5164 | Add tracking scheduler`
- `PLOG-5164 | HOTFIX | Fix null handling`
- `PLOG-5164 | Validation fixes`

From those commits it collects **added and modified line numbers** in `.java` files and runs rules only on those lines.

Lines untouched by the task are ignored, even if they violate a rule.

## Output

### Log (default)

One invalid finding per line:

```text
/absolute/path/File.java|42|Unused import 'Set'
```

### Task format

For the task file **Validation Findings** section:

```bash
javal PLOG-5164 --format task
```

```markdown
- [ ] `/absolute/path/File.java:42` — Unused import 'Set'
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings in task-scoped lines |
| `1` | One or more findings |
| `2` | Invalid arguments, missing repo, or not a git repository |

Progress and scope summary go to **stderr**; findings go to **stdout**.

## Rules

Each rule is a dedicated `JavaRule` class:

| Check | Description |
|-------|-------------|
| `unused-imports` | Import declared but not referenced |
| `java-naming-method-verb-prefix` | Method must start with allowed action verb |
| `java-naming-method-map-style` | Map-style method names without verb prefix |
| `java-naming-method-bare-participle` | Bare participles (`distinct`, `sorted`, …) |
| `java-naming-variable-collection-type` | `List` / `Set` / `Map` embedded in variable name |
| `java-naming-variable-hungarian` | Hungarian notation (`strName`, `intCount`, …) |
| `java-naming-constant-upper-snake` | Constants must use `UPPER_SNAKE_CASE` |

Naming rules follow `agents/rule-java-naming.md` from the workspace rules repo.

## Development

```bash
pip install -r requirements.txt
pytest
```

Fixture samples under `fixtures/java/` support unit tests. Task-scoped behaviour is covered by git fixture tests under `tests/`.

## Adding a rule

1. Create `validator/java/rules/<category>/<rule_name>.py` implementing `JavaRule`.
2. Register the class in `validator/java/rules/registry.py`.
3. Add a fixture Java sample and pytest coverage.
