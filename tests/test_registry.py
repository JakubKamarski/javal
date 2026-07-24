from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

from validator.analyze import analyze_repo
from validator.git_scope import TaskScope
from validator.java.rules.base import JavaRule, TreeJavaRule
from validator.java.rules.registry import (
    RULE_DESCRIPTIONS,
    all_registered_rules,
    discover_rule_module_paths,
    list_all_rule_meta,
    list_registered_rule_meta,
)
from validator.report import Finding, Report


RULES_ROOT = Path(__file__).resolve().parents[1] / "validator" / "java" / "rules"


class StubAnalyzer:
    def analyze(self, target, scope=None):
        return Report(
            target=str(target),
            task_id=scope.task_id if scope else "",
        )


def _module_import_path(path: Path) -> str:
    relative = path.relative_to(RULES_ROOT).with_suffix("")
    return "validator.java.rules." + ".".join(relative.parts)


def _rule_classes_in_module(module_path: Path) -> list[type[JavaRule | TreeJavaRule]]:
    module = importlib.import_module(_module_import_path(module_path))
    classes: list[type[JavaRule | TreeJavaRule]] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj is JavaRule or obj is TreeJavaRule:
            continue
        if issubclass(obj, (JavaRule, TreeJavaRule)) and obj.__module__ == module.__name__:
            classes.append(obj)
    return classes


def test_every_rule_module_defines_registered_rule():
    registered_ids = {rule.check_id for rule in all_registered_rules()}
    discovered_modules = discover_rule_module_paths(RULES_ROOT)

    assert discovered_modules, "expected at least one rule module"

    for module_path in discovered_modules:
        rule_classes = _rule_classes_in_module(module_path)
        assert rule_classes, f"No rule class found in {module_path.name}"
        for rule_class in rule_classes:
            instance = rule_class()
            assert instance.check_id in registered_ids, (
                f"{rule_class.__name__} ({instance.check_id}) is not registered"
            )


def test_registered_rules_have_descriptions():
    for meta in list_registered_rule_meta():
        assert meta.check_id in RULE_DESCRIPTIONS
        assert meta.description


def test_all_rule_inventory_includes_non_java_analyzers_without_duplicates():
    metadata = list_all_rule_meta()
    check_ids = [meta.check_id for meta in metadata]

    assert len(check_ids) == len(set(check_ids))
    assert check_ids[-3:] == [
        "liquibase-changeset-author",
        "git-uncommitted-changes",
        "git-commit-no-courier-symbol",
    ]


def test_tree_rules_declare_scope_policy():
    for rule in all_registered_rules():
        if isinstance(rule, TreeJavaRule):
            assert rule.scope_policy in {"task_changed", "global"}
            assert rule.meta.tree_scope == rule.scope_policy


def test_report_merge_combines_checks_and_findings():
    first = Report(target="/repo", task_id="ABC-1")
    first.add_check("rule-a")
    first.add_finding(
        Finding(severity="warning", check="rule-a", summary="first", file="/repo/A.java", line=1)
    )

    second = Report(target="/repo", task_id="ABC-1")
    second.add_check("rule-b")
    second.add_finding(
        Finding(severity="warning", check="rule-b", summary="second", file="/repo/B.java", line=2)
    )

    merged = Report.merge([first, second])

    assert merged.checks_run == ["rule-a", "rule-b"]
    assert len(merged.invalid_findings) == 2


def test_analyze_repo_accepts_prebuilt_scope(monkeypatch, tmp_path):
    calls: list[str] = []

    def fake_build_scope(repo, task_id):
        calls.append(task_id)
        return TaskScope(task_id=task_id, commits=(), changed_lines={}, line_authors={}, commit_changed_lines=())

    monkeypatch.setattr("validator.analyze.build_task_scope", fake_build_scope)

    scope = TaskScope(
        task_id="ABC-9999",
        commits=(),
        changed_lines={},
        line_authors={},
        commit_changed_lines=(),
    )
    report = analyze_repo(tmp_path, scope=scope, analyzers=(StubAnalyzer(),))

    assert calls == []
    assert report.task_id == "ABC-9999"


def test_analyze_repo_builds_scope_from_task_id_when_missing(monkeypatch, tmp_path):
    calls: list[str] = []

    def fake_build_scope(repo, task_id):
        calls.append(task_id)
        return TaskScope(task_id=task_id, commits=(), changed_lines={}, line_authors={}, commit_changed_lines=())

    monkeypatch.setattr("validator.analyze.build_task_scope", fake_build_scope)

    report = analyze_repo(tmp_path, task_id="ABC-1000", analyzers=(StubAnalyzer(),))

    assert calls == ["ABC-1000"]
    assert report.task_id == "ABC-1000"
