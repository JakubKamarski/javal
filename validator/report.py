from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning", "info"]
PathFormat = Literal["absolute", "relative", "filename"]


@dataclass
class Finding:
    severity: Severity
    check: str
    summary: str
    file: str = ""
    line: int = 0
    details: str = ""
    suggestion: str = ""

    @property
    def is_invalid(self) -> bool:
        return self.severity in {"error", "warning"} and bool(self.file)

    def display_path(
        self,
        repo_root: str | Path = "",
        path_format: PathFormat = "absolute",
    ) -> str:
        if not self.file:
            return ""
        file_path = Path(self.file).resolve()
        if path_format == "filename":
            return file_path.name
        if path_format == "relative" and repo_root:
            try:
                return str(file_path.relative_to(Path(repo_root).resolve()))
            except ValueError:
                pass
        return str(file_path)

    def log_line(
        self,
        repo_root: str | Path = "",
        path_format: PathFormat = "absolute",
    ) -> str:
        path = self.display_path(repo_root, path_format)
        line = self.line if self.line > 0 else 0
        return f"{path}|{line}|{self.summary}"

    def task_todo_line(
        self,
        repo_root: str | Path = "",
        done: bool = False,
        path_format: PathFormat = "absolute",
    ) -> str:
        path = self.display_path(repo_root, path_format)
        line = self.line if self.line > 0 else 0
        marker = "x" if done else " "
        return f"- [{marker}] `{path}:{line}` — {self.summary}"


@dataclass
class Report:
    target: str
    task_id: str = ""
    checks_run: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def invalid_findings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.is_invalid]

    @property
    def status(self) -> str:
        return "FAIL" if self.invalid_findings else "PASS"

    def add_check(self, name: str) -> None:
        if name not in self.checks_run:
            self.checks_run.append(name)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def add_pass(self, check: str, summary: str) -> None:
        self.add_finding(Finding(severity="info", check=check, summary=summary))

    @classmethod
    def merge(cls, reports: list[Report]) -> Report:
        if not reports:
            return cls(target="", task_id="")

        merged = cls(
            target=reports[0].target,
            task_id=reports[0].task_id,
        )
        for report in reports:
            if report.target and not merged.target:
                merged.target = report.target
            if report.task_id and not merged.task_id:
                merged.task_id = report.task_id
            for check in report.checks_run:
                merged.add_check(check)
            for finding in report.findings:
                merged.add_finding(finding)
        return merged

    def to_log_lines(self, path_format: PathFormat = "absolute") -> str:
        lines = [
            finding.log_line(self.target, path_format)
            for finding in self.invalid_findings
        ]
        return "\n".join(lines)

    def to_task_todos(self, path_format: PathFormat = "absolute") -> str:
        if not self.invalid_findings:
            return "- [x] No validation findings."
        return "\n".join(
            finding.task_todo_line(self.target, path_format=path_format)
            for finding in self.invalid_findings
        )

    def to_markdown(self, path_format: PathFormat = "absolute") -> str:
        lines = [
            "# Code Validation Report",
            "",
            f"**Target:** {self.target}",
        ]
        if self.task_id:
            lines.append(f"**Task:** {self.task_id}")
        lines.extend([
            f"**Status:** {self.status}",
            f"**Checks run:** {', '.join(self.checks_run) if self.checks_run else '(none)'}",
            "",
            "## Findings",
            "",
        ])

        actionable = [f for f in self.findings if f.severity != "info" or not f.file]
        info_only = [f for f in self.findings if f.severity == "info" and f.file]

        if not actionable and not info_only:
            lines.append("_No issues found._")
            return "\n".join(lines)

        for finding in actionable:
            lines.extend(self._format_finding(finding, self.target, path_format))

        passed = [f for f in self.findings if f.severity == "info" and not f.file]
        for finding in passed:
            lines.extend(self._format_finding(finding, self.target, path_format))

        return "\n".join(lines)

    def _format_finding(
        self,
        finding: Finding,
        repo_root: str | Path = "",
        path_format: PathFormat = "absolute",
    ) -> list[str]:
        block = [f"### [{finding.severity}] {finding.check}", ""]
        if finding.file:
            path = finding.display_path(repo_root, path_format)
            loc = f"{path}:{finding.line}" if finding.line else path
            block.append(f"- **location:** `{loc}`")
        block.append(f"- **summary:** {finding.summary}")
        if finding.details:
            block.extend(["- **details:**", "```text", finding.details, "```"])
        if finding.suggestion:
            block.append(f"- **suggestion:** {finding.suggestion}")
        block.append("")
        return block
