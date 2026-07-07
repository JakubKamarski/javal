#!/usr/bin/env bash
set -euo pipefail

# Compile a Maven project. Emits findings via report.sh (must be sourced by caller).

run_maven_compile_check() {
  local repo="$1"
  local quiet="${2:-false}"

  report_check_started "maven-compile"

  if [[ ! -f "${repo}/pom.xml" ]]; then
    report_finding "info" "maven-compile" "Skipped — no pom.xml at repository root" "" ""
    return 0
  fi

  local mvn_cmd="mvn"
  if ! command -v mvn >/dev/null 2>&1; then
    if [[ -x "${repo}/mvnw" ]]; then
      mvn_cmd="${repo}/mvnw"
    else
      report_finding "error" "maven-compile" "Maven not found and no mvnw wrapper present" "" "Install Maven or add the Maven wrapper to the project."
      return 1
    fi
  fi

  local log
  log="$(mktemp)"
  trap 'rm -f "${log}"' RETURN

  local mvn_args=(-q -DtrimStackTrace=true -Dstyle.color=never compile)
  if [[ "${quiet}" != "true" ]]; then
    echo "[maven-compile] running in ${repo}" >&2
  fi

  if (cd "${repo}" && "${mvn_cmd}" "${mvn_args[@]}" >"${log}" 2>&1); then
    report_check_passed "maven-compile" "Compilation succeeded"
    return 0
  fi

  local excerpt
  excerpt="$(tail -n 40 "${log}")"
  report_finding "error" "maven-compile" "Compilation failed" "${excerpt}" "Fix compile errors in the listed source files, then re-run validate.sh."
  return 1
}
