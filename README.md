# me-javal

Java validator CLI (`javal`) for task-scoped static analysis. Validates **only Java lines added or changed in task commits** on the current branch.

Complements [me-ai-coder](https://github.com/JakubKamarski/ai-coder) (rules, skills, specs).

## Workspace placement

Keep this repo under the workspace `projects/` folder:

```
~/work/projects/me-javal/
```

Clone name may vary; locate the repo by `validate.py` and `install.sh` at the repository root.

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

# Human-friendly relative paths
javal PLOG-5164 --path-format relative

# Filename-only paths
javal PLOG-5164 --path-format filename

# Markdown report
javal PLOG-5164 --format markdown worktrees/PLOG-5164/locus-fc-orlen

# Report a false-positive or validator bug (AI agents)
javal todo \
  --file /Users/you/work/projects/locus-fc-orlen/src/Foo.java \
  --line 42 \
  --description "False positive: unused-imports — Set is used via static import"
```

### Options

| Flag / command | Default | Description |
|----------------|---------|-------------|
| `--format` | `log` | Output layout: `log`, `markdown`, or `task` |
| `--path-format` | `absolute` | File path style: `absolute`, `relative`, or `filename` |
| `-q` / `--quiet` | off | Suppress progress on stderr |
| `javal todo` | — | Report false positive or validator bug (see below) |
| `javal list-rules` | — | List registered validation rules with scope and description |

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

**Exception:** `java-testing-duplicate-it-and-test` scans the whole repository for `*Test` + `*IT` pairs. If a task adds an IT file and a matching unit test already exists from an earlier task (or vice versa), the duplication is reported.

## Output

### Log (default)

One invalid finding per line:

```text
/Users/you/work/projects/locus-fc-orlen/src/main/java/File.java|42|Unused import 'Set'
```

Paths are **absolute** by default (for agents and tooling). Use `--path-format relative` or `--path-format filename` for shorter human-readable output.

### Task format

For the task file **Validation Findings** section:

```bash
javal PLOG-5164 --format task
```

```markdown
- [ ] `/Users/you/work/projects/locus-fc-orlen/src/main/java/File.java:42` — Unused import 'Set'
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings in task-scoped lines |
| `1` | One or more findings |
| `2` | Invalid arguments, missing repo, or not a git repository |

Progress and scope summary go to **stderr**; findings go to **stdout**.

## Report validator issues (for AI agents)

Use `javal todo` to log false positives or validator bugs to local `todo.md` in this repository (gitignored, not committed).

```bash
javal todo --file <path> --line <n> --description "<issue>"
```

Run `javal todo --help` for full flag reference.

### When to use

- Finding is a **false positive** — code is correct but javal flags it (e.g. static import not detected, missing framework exemption)
- Finding is a **validator bug** — rule logic is wrong, crashes, or reports the wrong line
- You verified the flagged line and rule name; description explains *why* javal is wrong

### When NOT to use

- Stylistic disagreement with a valid rule — fix the Java source instead
- Pre-existing violation on untouched lines (out of task scope) — ignore, do not report
- User explicitly approved an exception in the task file — document there, not in `todo.md`
- To avoid validation-fix work — never use `todo` to bypass the mandatory gate

### How agents should use it

1. Run `javal <TASK-ID>` and parse `path|line|description` from stdout
2. Inspect the flagged file at that line; confirm it is a false positive or bug (not a fixable violation)
3. Run `javal todo --file <absolute-path> --line <n> --description "<check>: <why javal is wrong>"`
4. Use the **same absolute path** from javal log output (default `--path-format absolute`)
5. Include the check/rule name in the description when known (e.g. `unused-imports`, `java-naming-method-verb-prefix`)
6. Continue the validation-fix workflow for **remaining real findings** — reporting one false positive does not clear the gate
7. Tell the user you reported a validator issue and that `todo.md` was updated locally

### Example

```bash
javal todo \
  --file /Users/you/work/projects/locus-fc-orlen/src/main/java/Foo.java \
  --line 42 \
  --description "False positive: unused-imports — Set is used via static import"
```

Stdout prints the appended markdown line; exit code `0` confirms success.

## Rules

Each rule is a dedicated `JavaRule` class:

| Check | Description |
|-------|-------------|
| `unused-imports` | Import declared but not referenced |
| `java-naming-method-verb-prefix` | Method must start with an action verb (with framework exemptions) |
| `java-naming-method-map-style` | Map-style method names without verb prefix |
| `java-naming-method-bare-participle` | Bare participles/adjectives (`distinct`, `sorted`, `empty`, …) |
| `java-naming-variable-collection-type` | `List` / `Set` / `Map` embedded in variable name |
| `java-naming-variable-hungarian` | Hungarian notation (`strName`, `intCount`, …) |
| `java-naming-local-variable-optional-prefix` | `Optional<...>` locals must use the `optional` prefix |
| `java-naming-constant-upper-snake` | Constants must use `UPPER_SNAKE_CASE` |
| `java-local-variable-no-var` | Local variables must use explicit types (`var` is forbidden) |
| `java-clean-code-comment` | Only `NOSONAR`, deprecation notes, public API javadoc, GWT markers, and task-referenced `TODO`/`FIXME` are allowed |
| `java-sonar-generic-type-nosonar` | Non-standard generic type parameter names require `NOSONAR` on the type header |
| `java-testing-when-generic-variable` | `// WHEN` locals must be descriptive; warns on generic names like `result` |
| `java-testing-duplicate-it-and-test` | Same subject has both `*Test` and `*IT` files in the repo — merge into the IT file (global scan; not limited to task-changed files) |
| `java-testing-missing-test-class` | Production classes covered by testing rules must have the required `*IT` or `*Test` counterpart (task-changed `src/main/java` files; fixture layout in unit tests). `*Repository` requires `*RepositoryIT` only when the task adds or changes a custom `@Query` method — derived query methods without `@Query` are excluded |
| `java-jpa-entity-serial-version-uid` | JPA `@Entity` persistent field changes in task scope must also update `serialVersionUID` |
| `git-uncommitted-changes` | Working tree has uncommitted changes — commit before finishing validation |
| `liquibase-changeset-author` | ChangeSet `author` must match the introducing task commit author; uncommitted changeSets use local `git config user.name` (task-introduced or uncommitted changeSets only — opening tag line in task diff or working tree) |

Naming rules follow `agents/rule-java-naming.md` from the workspace rules repo.
Testing structure rules follow `agents/rule-testing.md` from the workspace rules repo.

## Development

```bash
pip install -r requirements.txt
pytest
```

Fixture samples under `fixtures/` support unit tests. Task-scoped behaviour is covered by git fixture tests under `tests/`.

### Fixture and test-data conventions (MANDATORY)

- **Minimal**: Include only the smallest snippet that reproduces the behaviour under test.
- **Anonymized**: Use generic names (`Sample*`, `item-a`, `demo` packages). Never copy production classes, packages, waybills, or integration stacks from real repos.
- **Self-contained**: Keep data inside `fixtures/`; do not reference worktrees, `projects/locus-*`, or absolute paths to implementation repos in fixtures or pytest.
- **No production IT clones**: Do not paste WireMock/Spring/DB-heavy IT bodies into fixtures; model the parser/rule edge case with a few lines instead.
- **Guarded**: `tests/test_fixture_conventions.py` enforces the banned-pattern list; extend it when a new leak pattern appears.

When adding a rule, add a **minimal anonymized** fixture plus pytest coverage — not a trimmed copy of a task worktree file.

## Adding a rule

1. Copy [`validator/java/rules/_template.py`](validator/java/rules/_template.py) as a starting point.
2. Create `validator/java/rules/<category>/<rule_name>.py` implementing `JavaRule` or `TreeJavaRule`.
3. Register the class in `validator/java/rules/registry.py` and add a description to `RULE_DESCRIPTIONS`.
4. Add a minimal anonymized fixture sample and pytest coverage (see **Fixture and test-data conventions** above).

List registered rules:

```bash
javal list-rules
```

Tree rules use `scope_policy`:
- `task_changed` — only task-changed production files (default)
- `global` — whole repository scan (e.g. duplicate IT/Test detection)
