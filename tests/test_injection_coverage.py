from __future__ import annotations

import subprocess
from pathlib import Path

from validator.java.analyzer import analyze_java_tree

CHECK_ID = "java-testing-missing-test-class"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def test_analyze_java_tree_skips_internal_service_when_facade_it_exists(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    test_dir = tmp_path / "src" / "test" / "java" / "demo"
    main_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)

    (main_dir / "InternalShipmentService.java").write_text(
        "package demo;\n\nclass InternalShipmentService {\n"
        "    void persist() {}\n}\n",
        encoding="utf-8",
    )
    (main_dir / "SampleShipmentFacade.java").write_text(
        "package demo;\n\npublic class SampleShipmentFacade {\n"
        "    private final InternalShipmentService internalShipmentService;\n\n"
        "    public SampleShipmentFacade(InternalShipmentService internalShipmentService) {\n"
        "        this.internalShipmentService = internalShipmentService;\n"
        "    }\n}\n",
        encoding="utf-8",
    )
    (test_dir / "SampleShipmentFacadeIT.java").write_text(
        "package demo;\n\nclass SampleShipmentFacadeIT {\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add internal service covered by facade IT")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert all("InternalShipmentService" not in finding.summary for finding in findings)
