from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from validator.git_scope import TaskScope, collect_worktree_changed_lines, resolve_git_repo_root
from validator.java.ast.entities import (
    entity_class_name,
    find_jpa_entity_class,
    iter_jpa_entity_class_declarations,
    persistent_field_signatures,
    serial_version_uid_lines,
    serial_version_uid_value,
)
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import context_for
from validator.java.rules.base import TreeJavaRule
from validator.report import Finding

SUGGESTION = (
    "Regenerate serialVersionUID after changing persistent entity fields "
    "(see agents/rule-jpa.md)."
)


@dataclass(frozen=True)
class EntityState:
    persistent_fields: frozenset[tuple[str, str]]
    serial_version_uid: str


def _read_file_at_revision(repo_root: Path, revision: str, relative_path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{revision}:{relative_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _entity_state(source: str | None, path: str, class_name: str) -> EntityState | None:
    if source is None:
        return None
    context = JavaFileContext.from_source(path, source)
    entity = find_jpa_entity_class(context, class_name)
    if entity is None:
        return None
    return EntityState(
        persistent_fields=persistent_field_signatures(context, entity),
        serial_version_uid=serial_version_uid_value(context, entity),
    )


def _worktree_changed_lines(file_path: Path, repo_root: Path) -> set[int]:
    absolute_path = str(file_path.resolve())
    return collect_worktree_changed_lines(repo_root).get(absolute_path, set())


def _entity_sources_to_check(
    java_files: list[Path],
    scope: TaskScope,
    repo_root: Path,
) -> list[Path]:
    if not scope.commits:
        return []

    changed_paths = set(scope.changed_lines)
    for _commit, file_changes in scope.commit_changed_lines:
        changed_paths.update(file_changes)
    worktree_paths = set(collect_worktree_changed_lines(repo_root))

    return [
        path
        for path in java_files
        if str(path.resolve()) in changed_paths or str(path.resolve()) in worktree_paths
    ]


class EntitySerialVersionUidOnChangeRule(TreeJavaRule):
    scope_policy = "task_changed"
    tree_file_applicability = "production"

    @property
    def check_id(self) -> str:
        return "java-jpa-entity-serial-version-uid"

    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
        *,
        contexts: dict[str, JavaFileContext] | None = None,
    ) -> list[Finding]:
        if scope is None or not scope.commits:
            return []

        if not java_files:
            return []

        repo_root = resolve_git_repo_root(java_files[0])
        findings: list[Finding] = []
        reported: set[tuple[str, str]] = set()
        for source_path in _entity_sources_to_check(java_files, scope, repo_root):
            context = context_for(source_path, contexts)
            absolute_path = str(source_path.resolve())
            for entity in iter_jpa_entity_class_declarations(context):
                class_name = entity_class_name(context, entity)
                report_key = (absolute_path, class_name)
                if report_key in reported:
                    continue

                for finding in self._check_entity_commits(
                    context,
                    entity,
                    scope,
                    absolute_path,
                    repo_root,
                ):
                    findings.append(finding)
                    reported.add(report_key)
                    break

                if report_key in reported:
                    continue

                worktree_finding = self._check_entity_worktree(
                    context,
                    entity,
                    source_path,
                    absolute_path,
                    repo_root,
                )
                if worktree_finding is not None:
                    findings.append(worktree_finding)
                    reported.add(report_key)
        return findings

    def _check_entity_commits(
        self,
        context: JavaFileContext,
        entity_node,
        scope: TaskScope,
        absolute_path: str,
        repo_root: Path,
    ) -> list[Finding]:
        findings: list[Finding] = []
        serial_lines = serial_version_uid_lines(context, entity_node)
        class_name = entity_class_name(context, entity_node)
        relative_path = Path(absolute_path).relative_to(repo_root).as_posix()

        for commit, file_changes in scope.commit_changed_lines:
            if absolute_path not in file_changes:
                continue
            before_state = _entity_state(
                _read_file_at_revision(repo_root, f"{commit}^", relative_path),
                absolute_path,
                class_name,
            )
            after_state = _entity_state(
                _read_file_at_revision(repo_root, commit, relative_path),
                absolute_path,
                class_name,
            )
            finding = self._finding_for_state_change(
                class_name=class_name,
                before_state=before_state,
                after_state=after_state,
                serial_lines=serial_lines,
                fallback_line=entity_node.start_point[0] + 1,
                absolute_path=absolute_path,
            )
            if finding is not None:
                findings.append(finding)
        return findings

    def _check_entity_worktree(
        self,
        context: JavaFileContext,
        entity_node,
        source_path: Path,
        absolute_path: str,
        repo_root: Path,
    ) -> Finding | None:
        changed_lines = _worktree_changed_lines(source_path, repo_root)
        if not changed_lines:
            return None

        class_name = entity_class_name(context, entity_node)
        relative_path = source_path.relative_to(repo_root).as_posix()
        before_state = _entity_state(
            _read_file_at_revision(repo_root, "HEAD", relative_path),
            absolute_path,
            class_name,
        )
        after_state = EntityState(
            persistent_fields=persistent_field_signatures(context, entity_node),
            serial_version_uid=serial_version_uid_value(context, entity_node),
        )
        return self._finding_for_state_change(
            class_name=class_name,
            before_state=before_state,
            after_state=after_state,
            serial_lines=serial_version_uid_lines(context, entity_node),
            fallback_line=entity_node.start_point[0] + 1,
            absolute_path=absolute_path,
        )

    def _finding_for_state_change(
        self,
        *,
        class_name: str,
        before_state: EntityState | None,
        after_state: EntityState | None,
        serial_lines: set[int],
        fallback_line: int,
        absolute_path: str,
    ) -> Finding | None:
        if after_state is None:
            return None
        before_fields = before_state.persistent_fields if before_state is not None else frozenset()
        if before_fields == after_state.persistent_fields:
            return None
        before_serial = before_state.serial_version_uid if before_state is not None else ""
        if after_state.serial_version_uid and before_serial != after_state.serial_version_uid:
            return None
        if not after_state.serial_version_uid:
            return Finding(
                severity="warning",
                check=self.check_id,
                summary=(
                    f"Entity '{class_name}' changed persistent fields but is missing serialVersionUID."
                ),
                file=absolute_path,
                line=fallback_line,
                suggestion=SUGGESTION,
            )

        return Finding(
            severity="warning",
            check=self.check_id,
            summary=(
                f"Entity '{class_name}' changed persistent fields but serialVersionUID was not updated."
            ),
            file=absolute_path,
            line=min(serial_lines) if serial_lines else fallback_line,
            suggestion=SUGGESTION,
        )
