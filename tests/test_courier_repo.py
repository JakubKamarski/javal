from __future__ import annotations

from pathlib import Path

import pytest

from validator.courier_repo import (
    context_path_indicates_courier_dedicated_repo,
    find_main_application_config,
    is_courier_dedicated_repo,
    read_context_path,
    read_context_path_from_properties,
    read_context_path_from_yaml,
)


def test_read_context_path_from_properties_reads_server_servlet_context_path():
    content = """
# sample config
server.servlet.context-path=/locus-courier-sample/rs
spring.application.name=sample
"""
    assert read_context_path_from_properties(content) == "/locus-courier-sample/rs"


def test_read_context_path_from_yaml_reads_nested_context_path():
    content = """
server:
  servlet:
    context-path: /locus-courier-sample/rs
"""
    assert read_context_path_from_yaml(content) == "/locus-courier-sample/rs"


@pytest.mark.parametrize(
    ("context_path", "expected"),
    [
        ("/locus-courier-sample/rs", True),
        ("/locus-courier-fancourier2/rs", True),
        ("/locus-carrier-dpd/rs", False),
        ("/locus-dpd-services/rs", False),
        ("/", False),
    ],
)
def test_context_path_indicates_courier_dedicated_repo(context_path, expected):
    assert context_path_indicates_courier_dedicated_repo(context_path) is expected


def _write_courier_application_properties(repo: Path, courier_name: str = "sample") -> None:
    config_dir = repo / "src" / "main" / "resources"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "application.properties").write_text(
        f"server.servlet.context-path=/locus-courier-{courier_name}/rs\n",
        encoding="utf-8",
    )


def test_find_main_application_config_prefers_standard_layout(tmp_path):
    repo = tmp_path / "hermes"
    _write_courier_application_properties(repo, "hermes")

    config_path = find_main_application_config(repo)

    assert config_path == repo / "src" / "main" / "resources" / "application.properties"
    assert read_context_path(config_path) == "/locus-courier-hermes/rs"


@pytest.mark.parametrize(
    ("repo_name", "context_path", "expected"),
    [
        ("hermes", "/locus-courier-hermes/rs", True),
        ("fancourier-local", "/locus-courier-fancourier2/rs", True),
        ("shared-lib", None, False),
        ("carrier-dpd", "/locus-carrier-dpd/rs", False),
    ],
)
def test_is_courier_dedicated_repo_uses_application_properties(
    tmp_path,
    repo_name,
    context_path,
    expected,
):
    repo = tmp_path / repo_name
    repo.mkdir()
    if context_path is not None:
        config_dir = repo / "src" / "main" / "resources"
        config_dir.mkdir(parents=True)
        (config_dir / "application.properties").write_text(
            f"server.servlet.context-path={context_path}\n",
            encoding="utf-8",
        )

    assert is_courier_dedicated_repo(repo) is expected
