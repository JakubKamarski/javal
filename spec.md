# javal specification

This document defines the stable behavior and extension contracts of `javal`.
Installation and command examples belong in [README.md](README.md).

## Purpose

`javal` mechanically enforces selected Java, testing, JPA, Liquibase, and Git
workspace policies from
[me-ai-coder](https://github.com/JakubKamarski/ai-coder). Its primary consumers
are developers and agents validating a task before merge.

The CLI requires Python 3.10 or newer and a Git worktree. Java and XML inputs are
expected to be UTF-8.

## Behavioral contract

### Task identification

A task ID matches `^[A-Z][A-Z0-9]*-\d+$`. Reachable commits belong to the task
when their subject contains that standalone ID: it must not be preceded by an
alphanumeric character or followed by a digit. Conventional prefixes and separators
such as `fix: `, ` | `, a space, or `:` are accepted.

The CLI returns exit code `2` when no matching commit exists. Programmatic
analyzer APIs may still receive an empty `TaskScope` for isolated tests.

### Current-line scope

`TaskScope` exposes:

- `commits`: matching commits in chronological order.
- `changed_lines`: current absolute paths mapped to current `HEAD` line numbers.
- `line_authors`: the task commit author responsible for each current line.
- `commit_changed_lines`: the same current lines grouped by task commit. Changed
  paths remain present with an empty set when a commit only deletes content.

Scope construction works as follows:

1. Select matching commits with `git log --grep`.
2. Collect their changed paths with `git diff-tree`.
3. Run `git blame --line-porcelain HEAD` for current versions of those paths.
4. Retain lines attributed to a matching task commit.

This keeps findings aligned after later commits insert or remove lines. A line
subsequently replaced by a non-task commit no longer belongs to task scope.

File rules report only findings on `changed_lines`. Tree rules define their own
scope policy because some checks require repository context or before/after Git
snapshots.

### Worktree state

`git-uncommitted-changes` inspects porcelain-v1 NUL-delimited output and fails on
tracked or untracked changes. Binary untracked files are not decoded for line
scope, but they still make the repository dirty.

`git-commit-no-courier-symbol` runs only in courier-dedicated repositories
detected from `src/main/resources/application.properties` or `.yml`: when
`server.servlet.context-path` contains the `courier` keyword. It inspects task
commit subjects: after the task ID, only `<Capitalized message>` or
`HOTFIX | <Capitalized message>` pipe segments are allowed. Extra MR-style
courier or service segments fail validation. Deployment-config commits that
include `FC` or `DC` are exempt. In other repositories, courier symbol segments
in commit subjects are optional and not validated.

## Architecture

```text
validate.py
  -> TaskScope
  -> analyze_repo
       -> JavaAnalyzer
       -> LiquibaseAnalyzer
       -> GitWorkspaceAnalyzer
  -> Report.merge
  -> log, task, or Markdown output
```

Key modules:

```text
validator/
  analyze.py             analyzer orchestration
  git_scope.py           task commits and current-line attribution
  git_workspace.py       dirty-worktree validation
  report.py              findings, reports, and rendering
  java/
    analyzer.py          Java file and tree rule orchestration
    context.py           source, UTF-8 bytes, and parsed AST
    parser.py            tree-sitter-java wrapper
    ast/                 reusable syntax helpers
    rules/               rule contracts, registry, implementations
  liquibase/
    analyzer.py          task-aware changeSet author validation
    changeset.py         structural XML changeSet parser
```

Analyzers implement:

```python
analyze(target: Path, scope: TaskScope | None = None) -> Report
```

They are intentionally independent and own their discovery and checks. The
top-level orchestrator merges their reports.

## Java analysis

### Parsing and context

Java is parsed with `tree-sitter-java`. `JavaFileContext` stores the original
string, its UTF-8 bytes, and the parse root. Node text is sliced from the byte
buffer because tree-sitter offsets are byte offsets. No source normalization is
performed.

One context cache is used per `JavaAnalyzer` tree run. Rules should use
`context_for()` when a cached context may be available.

The analyzer is syntactic: it has no classpath, type resolution, compiler
symbols, or bytecode.

### Rule contracts

`JavaRule` validates one file:

```python
check_id: str
file_applicability: Literal["any", "test", "main", "production"]
applies_to(context: JavaFileContext) -> bool
apply(context: JavaFileContext) -> list[RuleViolation]
```

`TreeJavaRule` validates a repository view:

```python
check_id: str
scope_policy: Literal["task_changed", "global"]
tree_file_applicability: Literal["any", "test", "main", "production"]
apply_tree(java_files, scope, *, contexts) -> list[Finding]
```

Applicability is enforced by the orchestrator before a rule runs:

- `test`: `src/test/java`, `*Test.java`, or `*IT.java`.
- `main`: `src/main/java`.
- `production`: non-test main sources and source snippets outside a `src` tree.
- `any`: every discovered Java file.

Rules are registered explicitly in `validator/java/rules/registry.py`. Explicit
registration keeps order and descriptions deterministic. `javal list-rules` is
the authoritative inventory.

### Type declaration headers

`java-style-type-header-one-line` keeps class, interface, record, enum, and
annotation-type declarations on one physical line from their first modifier
through the opening brace when the compact form is at most 120 columns. Leading
annotations and Javadocs are excluded. The projected length preserves declaration
indentation and joins trimmed header lines with one space. Headers whose compact
form exceeds 120 columns may remain either single-line or multiline.

### Lombok simplifications

`java-lombok-required-args-constructor` flags a constructor only when it directly assigns
every uninitialized, non-static `final` field from identically named parameters and has no
annotations or other logic. `java-lombok-static-factory` flags a static factory only when it
is paired with that constructor shape and its sole action is to return a new enclosing-type
instance with those parameters forwarded unchanged. Both checks deliberately skip annotations,
initialized fields, argument transformations, validation, and any additional statement.

### Tree-rule specifics

- Duplicate `*Test` and `*IT` detection scans eligible test paths but reports only a pair newly introduced by a task commit.
- Missing-test detection starts from task-changed production classes. Injection
  coverage resolves types by package, explicit import, and source root; ambiguous
  same-named types do not grant coverage. An `IT` requirement is satisfied by any
  test file named after the subject and ending in `IT` (for example a
  `<Subject>MockedIT`), not only the exact `<Subject>IT`. A framework-free
  `*Service` — one with no Spring boundary annotation (`@Service`, `@Component`,
  `@Repository`, `@Controller`, `@RestController`, `@Configuration`,
  `@Transactional`, `@Entity`) — is exempt from the integration-test requirement
  when it has a unit `*Test`, matching the shared-library-logic testing policy.
- Entity validation compares persistent field signatures before and after each
  task commit. Added, removed, renamed, or retyped fields require a changed
  `serialVersionUID` in that commit. Worktree changes compare `HEAD` with the
  current source.

### Test and collection conventions

- Every `@Test` and `@ParameterizedTest` must contain exactly one ordered
  `// GIVEN`, `// WHEN`, and `// THEN` section.
- A test name starts with the method invoked in `// WHEN`.
- Equivalent normal-response and exception-path tests with the same resolvable
  invocation signature form one parameterized test; normal and exception outcomes
  stay separate.
- Exception tests capture `Throwable exception` with `catchThrowable` in `// WHEN`
  and assert it in `// THEN`.
- The receiver of that invocation is initialized in `// GIVEN`, is a directly
  initialized `final` field in the test class, or is an annotated non-static
  field in an integration test (`*IT` type or `*IT` slice annotation). The
  latter two forms cover stateless reusable owners and framework-managed test
  setup. A single meaningful callback action on a receiver type ending in
  `Template` is the tested invocation; ambiguous callbacks are ignored.
- Empty `List.of()`, `Map.of()`, and `Set.of()` calls use the corresponding
  `Collections.empty*()` factory instead.
- A direct, single-branch `if` guard that only throws `IllegalArgumentException`
  uses Apache Commons Lang `Validate`: `Validate.notNull` for null rejection and
  `Validate.isTrue` for other valid-condition checks.

## Liquibase analysis

Changelogs are XML files named `*-changelog.xml`, named `db-changelog.xml`, or
whose initial content identifies a `databaseChangeLog`.

ChangeSets are parsed with Python's namespace-aware Expat parser rather than
regular expressions. Attributes may span lines. Malformed XML produces a
finding at the parser line instead of a traceback.

For a task-introduced changeSet, `author` must match the responsible task commit
author case- and diacritic-insensitively. A person with a hyphenated surname may
use either surname component when the given name matches. An uncommitted changeSet
uses local `git config user.name`. Editing only the body of a pre-existing changeSet
does not revalidate its author.

## Reporting

A `Finding` contains severity, check ID, summary, path, line, optional details,
and an optional suggestion. Warnings and errors with a path fail validation.

Output formats:

- `log`: `path|line|summary`, one finding per line.
- `task`: Markdown checklist entries.
- `markdown`: a human-readable report.

Paths may be absolute, repository-relative, or filename-only. Progress is sent
to stderr and findings to stdout.

## Extension and testing

New Java rules must:

1. Implement `JavaRule` or `TreeJavaRule` in one focused module.
2. Declare the narrowest applicable path and tree scope.
3. Register the implementation and description explicitly.
4. Add minimal anonymized fixtures and one test per distinct behavior branch.

Repository tests cover rule behavior, Git-backed task scope, report formats,
fixture sanitization, and registry completeness. Run `pytest -q` before commit.

## Known limitations

- Java checks are syntactic heuristics and cannot replace compilation or a
  semantic analyzer.
- Some tree rules inspect or parse the full repository even during task-scoped
  validation; large monorepos may incur noticeable startup cost.
- File discovery filters build directories after `Path.rglob` traversal rather
  than pruning them before descent.
- Dependencies use lower bounds without a lock file, and installers use the
  active Python environment rather than an isolated package installation.
- The repository has no committed CI, lint, or type-check configuration; pytest
  is currently the only automated quality gate.
