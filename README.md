# javal

`javal` is a task-scoped static-analysis CLI for Java repositories. It validates
current lines introduced by commits whose subject contains a standalone task ID, plus a
small set of repository-wide and worktree checks.

The enforced policies come from
[me-ai-coder](https://github.com/JakubKamarski/ai-coder). For design details and
extension contracts, see [spec.md](spec.md).

## Requirements

- Python 3.10 or newer
- Git
- A Git repository whose task commits contain an ID such as `ABC-1234`

## Install

macOS, Linux, or Git Bash:

```bash
./install.sh
```

Windows PowerShell:

```powershell
./install.ps1
```

The installer adds a `javal` launcher to `~/.local/bin` or `~/bin` and installs
the dependencies from `requirements.txt`. The launcher points to this checkout,
so do not move or delete it after installation.

Uninstall with the matching script:

```bash
./uninstall.sh
```

## Usage

```bash
javal <TASK-ID> [repo-path]
```

`repo-path` defaults to the current directory. A nested path is accepted and is
resolved to its Git repository root.

```bash
# Validate the current repository
javal ABC-1234

# Produce task-file checklist output
javal ABC-1234 --format task

# Use repository-relative paths
javal ABC-1234 --path-format relative

# Produce a Markdown report
javal ABC-1234 --format markdown /path/to/repository

# Inspect the live rule registry
javal list-rules
```

### Options

| Option | Values | Default |
|---|---|---|
| `--format` | `log`, `task`, `markdown` | `log` |
| `--path-format` | `absolute`, `relative`, `filename` | `absolute` |
| `-q`, `--quiet` | Suppress progress output | off |

### Task scope

Commit subjects may place the task ID anywhere as a standalone identifier:

```text
ABC-1234 | Add tracking scheduler
ABC-1234 Add tracking scheduler
ABC-1234: Fix null handling
fix: ABC-1234 Handle timeout
```

File rules run on current `HEAD` lines attributed to matching task commits.
Tree rules may inspect broader context when their contract requires it, for
example to determine whether a task newly introduced a duplicate test-file pair
or changed entity fields. Any uncommitted file makes validation fail. A task ID
with no matching commits is an input error.

### Output and exit codes

Default output contains one finding per line:

```text
/absolute/path/File.java|42|Unused import 'Set'
```

Progress goes to stderr; findings go to stdout.

| Code | Meaning |
|---|---|
| `0` | Validation passed |
| `1` | One or more findings |
| `2` | Invalid input, no task commits, or invalid repository |

## Reporting validator issues

Use `todo` only for a confirmed false positive or validator defect, not to bypass
a valid finding:

```bash
javal todo \
  --file /absolute/path/File.java \
  --line 42 \
  --description "unused-imports: imported type is referenced by valid code"
```

The command appends the report to the checkout-local, ignored `todo.md` file.

## Development

```bash
python -m pip install -r requirements.txt
pytest -q
```

To add a Java rule:

1. Copy `validator/java/rules/_template.py` into the appropriate category.
2. Implement `JavaRule` or `TreeJavaRule`.
3. Register it in `validator/java/rules/registry.py` with a description.
4. Add a minimal, anonymized fixture and focused pytest coverage.

Run `javal list-rules` for the authoritative list of checks. See
[spec.md](spec.md) for applicability, scope, parsing, and testing contracts.
