#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/lib/report.sh"
source "${SCRIPT_DIR}/checks/maven-compile.sh"
source "${SCRIPT_DIR}/checks/maven-test.sh"

usage() {
  cat <<'EOF'
Usage: validate.sh [options] <repo-path>

Run validation checks and print an AI-readable Markdown report.

Options:
  -t, --test CLASS   Run a specific Maven test class (repeatable)
  -q, --quiet        Suppress progress messages on stderr
  -h, --help         Show this help

Examples:
  validate.sh ~/work/projects/locus-fc-orlen
  validate.sh -t OrlenTrackingSchedulerTest ~/work/projects/locus-fc-orlen
EOF
}

resolve_repo_path() {
  local path="$1"
  if [[ -d "${path}" ]]; then
    (cd "${path}" && pwd)
  else
    echo "Error: not a directory: ${path}" >&2
    exit 1
  fi
}

main() {
  local quiet=false
  local -a test_classes=()
  local repo=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -t|--test)
        shift
        [[ $# -gt 0 ]] || { echo "Error: -t requires a test class name" >&2; exit 1; }
        test_classes+=("$1")
        shift
        ;;
      -q|--quiet)
        quiet=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "Error: unknown option: $1" >&2
        usage >&2
        exit 1
        ;;
      *)
        repo="$1"
        shift
        break
        ;;
    esac
  done

  if [[ -z "${repo}" && $# -gt 0 ]]; then
    repo="$1"
    shift
  fi

  if [[ -z "${repo}" ]]; then
    echo "Error: repository path required" >&2
    usage >&2
    exit 1
  fi

  local target
  target="$(resolve_repo_path "${repo}")"

  run_maven_compile_check "${target}" "${quiet}" || true
  run_maven_test_check "${target}" "${quiet}" "${test_classes[@]}" || true

  emit_report "${target}"

  if [[ "${REPORT_STATUS}" == "FAIL" ]]; then
    exit 1
  fi
}

main "$@"
