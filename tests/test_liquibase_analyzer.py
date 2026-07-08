from __future__ import annotations

import subprocess
from pathlib import Path

from validator.analyze import analyze_repo
from validator.git_scope import parse_unified_diff
from validator.liquibase.changeset import parse_changesets

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "liquibase"

SAMPLE_CHANGELOG_DIFF = """\
diff --git a/src/main/resources/app-db-changelog.xml b/src/main/resources/app-db-changelog.xml
index 1111111..2222222 100644
--- a/src/main/resources/app-db-changelog.xml
+++ b/src/main/resources/app-db-changelog.xml
@@ -0,0 +1,6 @@
+<databaseChangeLog>
+    <changeSet id="2026-07-07-add-sample-table" author="Wrong Author">
+        <createTable tableName="Sample"/>
+    </changeSet>
+</databaseChangeLog>
"""


def test_parse_unified_diff_collects_xml_files():
    changed = parse_unified_diff(SAMPLE_CHANGELOG_DIFF)
    assert changed == {
        "src/main/resources/app-db-changelog.xml": {1, 2, 3, 4, 5, 6},
    }


def test_parse_changesets_extracts_author_and_line_range():
    source = FIXTURES_DIR.joinpath("bad-author-changelog.xml").read_text(encoding="utf-8")
    changesets = parse_changesets(source)

    assert len(changesets) == 1
    assert changesets[0].changeset_id == "2026-07-07-add-sample-table"
    assert changesets[0].author == "Wrong Author"
    assert changesets[0].start_line == 5
    assert changesets[0].end_line == 9


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _init_repo_with_changelog_commit(repo: Path, task_id: str) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    changelog_dir = repo / "src/main/resources"
    changelog_dir.mkdir(parents=True)
    (changelog_dir / "app-db-changelog.xml").write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"base\" author=\"Test User\">\n"
        "        <sql>SELECT 1</sql>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")

    (changelog_dir / "app-db-changelog.xml").write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"base\" author=\"Test User\">\n"
        "        <sql>SELECT 1</sql>\n"
        "    </changeSet>\n"
        "    <changeSet id=\"2026-07-07-add-sample-table\" author=\"Wrong Author\">\n"
        "        <createTable tableName=\"Sample\"/>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"{task_id} | Add changelog")


def test_analyze_repo_flags_wrong_author_on_new_changeset(tmp_path):
    task_id = "PLOG-8888"
    _init_repo_with_changelog_commit(tmp_path, task_id)

    report = analyze_repo(tmp_path, task_id=task_id)

    liquibase_findings = [
        finding for finding in report.invalid_findings if finding.check == "liquibase-changeset-author"
    ]
    assert len(liquibase_findings) == 1
    assert "Wrong Author" in liquibase_findings[0].summary
    assert "Test User" in liquibase_findings[0].summary
    assert "commit author" in liquibase_findings[0].summary
    assert liquibase_findings[0].display_path(tmp_path).endswith("app-db-changelog.xml")


def _init_repo_with_preexisting_changeset(repo: Path, task_id: str) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    changelog_dir = repo / "src/main/resources"
    changelog_dir.mkdir(parents=True)
    (changelog_dir / "app-db-changelog.xml").write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"2026-07-02-add-sample-table\" author=\"Wrong Author\">\n"
        "        <createTable tableName=\"Sample\">\n"
        "            <column name=\"id\" type=\"BIGINT\"/>\n"
        "        </createTable>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "PLOG-5162 | Add sample table")

    (changelog_dir / "app-db-changelog.xml").write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"2026-07-02-add-sample-table\" author=\"Wrong Author\">\n"
        "        <createTable tableName=\"Sample\">\n"
        "            <column name=\"id\" type=\"BIGINT\"/>\n"
        "        </createTable>\n"
        "        <insert tableName=\"Sample\">\n"
        "            <column name=\"id\" valueNumeric=\"1\"/>\n"
        "        </insert>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"{task_id} | Add seed row")


def test_skips_author_on_preexisting_changeset(tmp_path):
    task_id = "PLOG-5164"
    _init_repo_with_preexisting_changeset(tmp_path, task_id)

    report = analyze_repo(tmp_path, task_id=task_id)

    liquibase_findings = [
        finding for finding in report.invalid_findings if finding.check == "liquibase-changeset-author"
    ]
    assert liquibase_findings == []


def test_flags_author_when_opening_tag_changed(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    changelog_dir = tmp_path / "src/main/resources"
    changelog_dir.mkdir(parents=True)
    changelog_path = changelog_dir / "app-db-changelog.xml"
    changelog_path.write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"2026-07-07-add-sample-table\" author=\"Wrong Author\">\n"
        "        <createTable tableName=\"Sample\"/>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")

    changelog_path.write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"2026-07-07-add-sample-table\" author=\"Still Wrong\">\n"
        "        <createTable tableName=\"Sample\"/>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Fix author")

    report = analyze_repo(tmp_path, task_id=task_id)

    liquibase_findings = [
        finding for finding in report.invalid_findings if finding.check == "liquibase-changeset-author"
    ]
    assert len(liquibase_findings) == 1
    assert "Still Wrong" in liquibase_findings[0].summary


def test_accepts_changeset_author_matching_commit_author_not_local_git_config(tmp_path):
    task_id = "PLOG-5130"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "jakub@example.com")
    _git(tmp_path, "config", "user.name", "Jakub Kamarski")

    changelog_dir = tmp_path / "db"
    changelog_dir.mkdir()
    changelog_path = changelog_dir / "dhl-db-changelog.xml"
    changelog_path.write_text(
        "<databaseChangeLog>\n</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(tmp_path, "config", "user.name", "Daniel Szuta")
    _git(tmp_path, "config", "user.email", "daniel@example.com")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")

    changelog_path.write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"2026-07-08-add-table\" author=\"Daniel Szuta\">\n"
        "        <createTable tableName=\"Sample\"/>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add changelog")

    _git(tmp_path, "config", "user.name", "Jakub Kamarski")
    _git(tmp_path, "config", "user.email", "jakub@example.com")

    report = analyze_repo(tmp_path, task_id=task_id)

    liquibase_findings = [
        finding for finding in report.invalid_findings if finding.check == "liquibase-changeset-author"
    ]
    assert liquibase_findings == []


def test_flags_wrong_author_on_uncommitted_changeset_using_local_git_config(tmp_path):
    task_id = "PLOG-7777"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    changelog_dir = tmp_path / "src/main/resources"
    changelog_dir.mkdir(parents=True)
    changelog_path = changelog_dir / "app-db-changelog.xml"
    changelog_path.write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"base\" author=\"Test User\">\n"
        "        <sql>SELECT 1</sql>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Initial changelog")

    changelog_path.write_text(
        "<databaseChangeLog>\n"
        "    <changeSet id=\"base\" author=\"Test User\">\n"
        "        <sql>SELECT 1</sql>\n"
        "    </changeSet>\n"
        "    <changeSet id=\"2026-07-08-add-sample-table\" author=\"Wrong Author\">\n"
        "        <createTable tableName=\"Sample\"/>\n"
        "    </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )

    report = analyze_repo(tmp_path, task_id=task_id)

    liquibase_findings = [
        finding for finding in report.invalid_findings if finding.check == "liquibase-changeset-author"
    ]
    assert len(liquibase_findings) == 1
    assert "Wrong Author" in liquibase_findings[0].summary
    assert "Test User" in liquibase_findings[0].summary
    assert "git user.name" in liquibase_findings[0].summary
