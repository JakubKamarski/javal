from __future__ import annotations

import subprocess
from pathlib import Path

from validator.java.analyzer import analyze_java_tree

CHECK_ID = "java-testing-missing-test-class"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def test_analyze_java_tree_skips_internal_service_when_facade_it_exists(tmp_path):
    task_id = "ABC-9999"
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


def test_same_named_service_in_other_package_is_not_covered_by_facade_it(tmp_path):
    task_id = "ABC-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    module_a_main = tmp_path / "module-a" / "src" / "main" / "java" / "first"
    module_a_test = tmp_path / "module-a" / "src" / "test" / "java" / "first"
    module_b_main = tmp_path / "module-b" / "src" / "main" / "java" / "second"
    module_a_main.mkdir(parents=True)
    module_a_test.mkdir(parents=True)
    module_b_main.mkdir(parents=True)

    (module_a_main / "InternalService.java").write_text(
        "package first;\nclass InternalService {}\n",
        encoding="utf-8",
    )
    (module_a_main / "SampleFacade.java").write_text(
        "package first;\npublic class SampleFacade {\n"
        "    private final InternalService service;\n"
        "    SampleFacade(InternalService service) { this.service = service; }\n"
        "}\n",
        encoding="utf-8",
    )
    (module_a_test / "SampleFacadeIT.java").write_text(
        "package first;\nclass SampleFacadeIT {}\n",
        encoding="utf-8",
    )
    other_service = module_b_main / "InternalService.java"
    other_service.write_text(
        "package second;\nclass InternalService {}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")

    other_service.write_text(
        "package second;\nclass InternalService {\n    void process() {}\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Change second service")

    report = analyze_java_tree(tmp_path, task_id=task_id)

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert any("InternalService" in finding.summary for finding in findings)
    assert any("module-b" in finding.file for finding in findings)
