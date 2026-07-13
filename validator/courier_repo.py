from __future__ import annotations

import re
from pathlib import Path

CONTEXT_PATH_PROPERTY = "server.servlet.context-path"
MAIN_APPLICATION_CONFIGS = (
    Path("src/main/resources/application.properties"),
    Path("src/main/resources/application.yml"),
    Path("src/main/resources/application.yaml"),
)
CONTEXT_PATH_YAML_PATTERN = re.compile(
    r"(?:server\.servlet\.context-path|context-path)\s*[:=]\s*['\"]?([^'\"\s#]+)",
    re.IGNORECASE,
)
COURIER_KEYWORD_PATTERN = re.compile(r"courier", re.IGNORECASE)


def find_main_application_config(repo: Path) -> Path | None:
    resolved_repo = repo.resolve()
    for relative_path in MAIN_APPLICATION_CONFIGS:
        candidate = resolved_repo / relative_path
        if candidate.is_file():
            return candidate

    for relative_path in MAIN_APPLICATION_CONFIGS:
        matches = sorted(resolved_repo.rglob(relative_path.name))
        for candidate in matches:
            if candidate.parent.name == "resources" and candidate.parent.parent.name == "main":
                return candidate
    return None


def read_context_path_from_properties(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        key, separator, value = stripped.partition("=")
        if separator and key.strip() == CONTEXT_PATH_PROPERTY:
            return value.strip()
    return None


def read_context_path_from_yaml(content: str) -> str | None:
    match = CONTEXT_PATH_YAML_PATTERN.search(content)
    if match is None:
        return None
    return match.group(1).strip()


def read_context_path(config_path: Path) -> str | None:
    content = config_path.read_text(encoding="utf-8")
    if config_path.suffix == ".properties":
        return read_context_path_from_properties(content)
    return read_context_path_from_yaml(content)


def context_path_indicates_courier_dedicated_repo(context_path: str) -> bool:
    return bool(COURIER_KEYWORD_PATTERN.search(context_path))


def is_courier_dedicated_repo(repo: Path) -> bool:
    config_path = find_main_application_config(repo)
    if config_path is None:
        return False
    context_path = read_context_path(config_path)
    if not context_path:
        return False
    return context_path_indicates_courier_dedicated_repo(context_path)
