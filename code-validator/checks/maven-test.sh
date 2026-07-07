#!/usr/bin/env bash
set -euo pipefail

# Run Maven tests — explicit class via -t or inferred from git diff.

infer_test_classes_from_diff() {
  local repo="$1"
  if ! git -C "${repo}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  {
    git -C "${repo}" diff --name-only HEAD 2>/dev/null || true
    git -C "${repo}" diff --name-only --cached 2>/dev/null || true
  } | sort -u | while IFS= read -r file; do
      [[ "${file}" == *Test.java ]] || continue
      basename "${file}" .java
    done
}

collect_test_classes() {
  local repo="$1"
  shift
  local -a explicit=("$@")
  local -a inferred=()
  local -a result=()
  local cls

  if ((${#explicit[@]} > 0)); then
    printf '%s\n' "${explicit[@]}"
    return 0
  fi

  while IFS= read -r cls; do
    [[ -n "${cls}" ]] && inferred+=("${cls}")
  done < <(infer_test_classes_from_diff "${repo}")

  if ((${#inferred[@]} == 0)); then
    return 0
  fi

  # Deduplicate
  for cls in "${inferred[@]}"; do
    local seen=false
    for existing in "${result[@]:-}"; do
      [[ "${existing}" == "${cls}" ]] && seen=true && break
    done
    [[ "${seen}" == "false" ]] && result+=("${cls}")
  done

  printf '%s\n' "${result[@]}"
}

run_maven_test_check() {
  local repo="$1"
  local quiet="${2:-false}"
  shift 2
  local -a test_classes=("$@")

  report_check_started "maven-test"

  if [[ ! -f "${repo}/pom.xml" ]]; then
    report_finding "info" "maven-test" "Skipped — no pom.xml at repository root" "" ""
    return 0
  fi

  local -a classes=()
  while IFS= read -r cls; do
    [[ -n "${cls}" ]] && classes+=("${cls}")
  done < <(collect_test_classes "${repo}" "${test_classes[@]:-}")

  if ((${#classes[@]} == 0)); then
    report_finding "info" "maven-test" "Skipped — no test class specified and none inferred from git diff" "" "Pass -t TestClassName or stage/commit test-related changes."
    return 0
  fi

  local mvn_cmd="mvn"
  if ! command -v mvn >/dev/null 2>&1; then
    if [[ -x "${repo}/mvnw" ]]; then
      mvn_cmd="${repo}/mvnw"
    else
      report_finding "error" "maven-test" "Maven not found and no mvnw wrapper present" "" "Install Maven or add the Maven wrapper to the project."
      return 1
    fi
  fi

  local test_arg
  test_arg="$(IFS=,; echo "${classes[*]}")"

  local log
  log="$(mktemp)"
  trap 'rm -f "${log}"' RETURN

  local mvn_args=(-q -DtrimStackTrace=true -Dstyle.color=never "-Dtest=${test_arg}" test)
  if [[ "${quiet}" != "true" ]]; then
    echo "[maven-test] running -Dtest=${test_arg} in ${repo}" >&2
  fi

  if (cd "${repo}" && "${mvn_cmd}" "${mvn_args[@]}" >"${log}" 2>&1); then
    report_check_passed "maven-test" "Tests passed (${test_arg})"
    return 0
  fi

  local excerpt
  excerpt="$(tail -n 60 "${log}")"
  report_finding "error" "maven-test" "Tests failed (${test_arg})" "${excerpt}" "Fix failing assertions or production code, then re-run validate.sh."
  return 1
}
