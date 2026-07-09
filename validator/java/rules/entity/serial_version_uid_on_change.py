from __future__ import annotations

from pathlib import Path

from validator.git_scope import TaskScope, collect_worktree_changed_lines, resolve_git_repo_root
from validator.java.ast.entities import (
    entity_class_name,
    iter_jpa_entity_class_declarations,
    persistent_field_lines,
    serial_version_uid_lines,
)
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import context_for
from validator.java.rules.base import TreeJavaRule
from validator.report import Finding

SUGGESTION = (
    "Regenerate serialVersionUID after changing persistent entity fields "
    "(see agents/rule-jpa.md)."
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
            if "@Entity" not in context.source:
                continue

            absolute_path = str(source_path.resolve())
            for entity in iter_jpa_entity_class_declarations(context):
                class_name = entity_class_name(context, entity)
                report_key = (absolute_path, class_name)
                if report_key in reported:
                    continue

                for finding in self._check_entity_commits(
                    context, entity, scope, absolute_path
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
    ) -> list[Finding]:
        findings: list[Finding] = []
        persistent_lines = persistent_field_lines(context, entity_node)
        serial_lines = serial_version_uid_lines(context, entity_node)
        class_name = entity_class_name(context, entity_node)

        for _commit, file_changes in scope.commit_changed_lines:
            changed_lines = file_changes.get(absolute_path, set())
            if not changed_lines:
                continue
            finding = self._finding_for_change_set(
                class_name=class_name,
                changed_persistent_lines=persistent_lines & changed_lines,
                changed_serial_lines=serial_lines & changed_lines,
                serial_lines=serial_lines,
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

        return self._finding_for_change_set(
            class_name=entity_class_name(context, entity_node),
            changed_persistent_lines=persistent_field_lines(context, entity_node) & changed_lines,
            changed_serial_lines=serial_version_uid_lines(context, entity_node) & changed_lines,
            serial_lines=serial_version_uid_lines(context, entity_node),
            absolute_path=absolute_path,
        )

    def _finding_for_change_set(
        self,
        *,
        class_name: str,
        changed_persistent_lines: set[int],
        changed_serial_lines: set[int],
        serial_lines: set[int],
        absolute_path: str,
    ) -> Finding | None:
        if not changed_persistent_lines:
            return None
        if changed_serial_lines:
            return None
        if not serial_lines:
            return Finding(
                severity="warning",
                check=self.check_id,
                summary=(
                    f"Entity '{class_name}' changed persistent fields but is missing serialVersionUID."
                ),
                file=absolute_path,
                line=min(changed_persistent_lines),
                suggestion=SUGGESTION,
            )

        return Finding(
            severity="warning",
            check=self.check_id,
            summary=(
                f"Entity '{class_name}' changed persistent fields but serialVersionUID was not updated."
            ),
            file=absolute_path,
            line=min(serial_lines),
            suggestion=SUGGESTION,
        )
