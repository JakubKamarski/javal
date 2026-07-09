from __future__ import annotations

import subprocess
from pathlib import Path

from validator.git_scope import TaskScope, build_task_scope
from validator.java.analyzer import JavaAnalyzer, analyze_java_tree
from validator.java.ast import (
    iter_jpa_entity_class_declarations,
    persistent_field_lines,
    serial_version_uid_lines,
)
from validator.java.context import JavaFileContext
from validator.java.rules.entity.serial_version_uid_on_change import EntitySerialVersionUidOnChangeRule

CHECK_ID = "java-jpa-entity-serial-version-uid"
ENTITY_SOURCE = """\
package demo;

import jakarta.persistence.Entity;

@Entity
class SampleEntity {

    private static final long serialVersionUID = 1L;

    private String name;
}
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _write_entity(path: Path, serial_uid: str, fields: str) -> None:
    path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n\n"
        f"    private static final long serialVersionUID = {serial_uid};\n\n"
        f"{fields}"
        "}\n",
        encoding="utf-8",
    )


def test_entity_ast_detects_persistent_fields_and_serial_version_uid():
    context = JavaFileContext.from_source("SampleEntity.java", ENTITY_SOURCE)
    entity = next(iter(iter_jpa_entity_class_declarations(context)))

    assert persistent_field_lines(context, entity) == {10}
    assert serial_version_uid_lines(context, entity) == {8}


def test_flags_entity_when_persistent_field_changes_without_serial_version_uid_update(tmp_path):
    task_id = "ABC-8888"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    entity_path = main_dir / "SampleEntity.java"
    _write_entity(entity_path, "1L", "    private String name;\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add entity")

    _write_entity(entity_path, "1L", "    private String name;\n    private String code;\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add code field")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert "serialVersionUID was not updated" in findings[0].summary


def test_passes_when_serial_version_uid_is_updated_with_field_change(tmp_path):
    task_id = "ABC-8888"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    entity_path = main_dir / "SampleEntity.java"
    _write_entity(entity_path, "1L", "    private String name;\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add entity")

    _write_entity(entity_path, "2L", "    private String name;\n    private String code;\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add code field")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert findings == []


def test_ignores_method_only_entity_changes(tmp_path):
    task_id = "ABC-8888"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    entity_path = main_dir / "SampleEntity.java"
    entity_path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n\n"
        "    private static final long serialVersionUID = 1L;\n\n"
        "    private String name;\n\n"
        "    public String getName() {\n"
        "        return name;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add entity")

    entity_path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n\n"
        "    private static final long serialVersionUID = 1L;\n\n"
        "    private String name;\n\n"
        "    public String getName() {\n"
        "        return name;\n"
        "    }\n\n"
        "    public void setName(String name) {\n"
        "        this.name = name;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add setter")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert findings == []


def test_flags_uncommitted_persistent_field_change_without_serial_version_uid_update(tmp_path):
    task_id = "ABC-8888"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    entity_path = main_dir / "SampleEntity.java"
    _write_entity(entity_path, "1L", "    private String name;\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add entity")

    _write_entity(entity_path, "1L", "    private String name;\n    private String code;\n")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert "serialVersionUID was not updated" in findings[0].summary


def test_flags_missing_serial_version_uid_when_persistent_field_changes(tmp_path):
    task_id = "ABC-8888"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    entity_path = main_dir / "SampleEntity.java"
    entity_path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n"
        "    private String name;\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add entity")

    entity_path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n"
        "    private String name;\n"
        "    private String code;\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add code field")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert "missing serialVersionUID" in findings[0].summary


def test_rule_directly_flags_missing_serial_version_uid(tmp_path):
    entity_path = tmp_path / "src" / "main" / "java" / "demo" / "SampleEntity.java"
    entity_path.parent.mkdir(parents=True)
    entity_path.write_text(
        "package demo;\n\n"
        "import jakarta.persistence.Entity;\n\n"
        "@Entity\n"
        "class SampleEntity {\n"
        "    private String name;\n"
        "    private String code;\n"
        "}\n",
        encoding="utf-8",
    )

    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "ABC-8888 | Add entity")

    scope = build_task_scope(tmp_path, "ABC-8888")
    analyzer = JavaAnalyzer(tree_rules=[EntitySerialVersionUidOnChangeRule()])
    report = analyzer.analyze_tree(tmp_path, scope=scope)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert "missing serialVersionUID" in findings[0].summary
