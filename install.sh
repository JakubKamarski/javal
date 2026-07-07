#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="${SCRIPT_DIR}/validate.py"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
UNAME_S="$(uname -s | tr '[:upper:]' '[:lower:]')"

case "${UNAME_S}" in
  mingw*|msys*|cygwin*)
    BIN_DIR="${HOME}/bin"
    ;;
  *)
    BIN_DIR="${HOME}/.local/bin"
    ;;
esac

COMMAND_NAME="javal"
COMMAND_PATH="${BIN_DIR}/${COMMAND_NAME}"

if [[ ! -f "${TARGET_SCRIPT}" ]]; then
  echo "Cannot find target script: ${TARGET_SCRIPT}" >&2
  exit 1
fi

mkdir -p "${BIN_DIR}"

install_python_deps() {
  local python_cmd="$1"
  if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
    return 0
  fi
  echo "Installing Python dependencies..."
  "${python_cmd}" -m pip install -r "${REQUIREMENTS_FILE}"
}

resolve_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v py >/dev/null 2>&1; then
    echo "py -3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  return 1
}

PYTHON_CMD="$(resolve_python || true)"
if [[ -z "${PYTHON_CMD}" ]]; then
  echo "Python interpreter not found. Install Python 3.8+ and re-run install.sh." >&2
  exit 1
fi

# shellcheck disable=SC2086
install_python_deps ${PYTHON_CMD}

cat > "${COMMAND_PATH}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
TARGET_SCRIPT="${TARGET_SCRIPT}"
CODE_VALIDATOR_DIR="${SCRIPT_DIR}"

export PYTHONPATH="\${CODE_VALIDATOR_DIR}:\${PYTHONPATH:-}"

if command -v python3 >/dev/null 2>&1; then
  python3 "\${TARGET_SCRIPT}" "\$@"
  exit \$?
fi

if command -v py >/dev/null 2>&1; then
  py -3 "\${TARGET_SCRIPT}" "\$@"
  exit \$?
fi

if command -v python >/dev/null 2>&1; then
  python "\${TARGET_SCRIPT}" "\$@"
  exit \$?
fi

echo "Python interpreter not found. Install Python or add py/python/python3 to PATH." >&2
exit 1
EOF

chmod +x "${COMMAND_PATH}"

echo "Installed launcher: ${COMMAND_PATH}"

case ":${PATH}:" in
  *":${BIN_DIR}:"*)
    echo "PATH already contains ${BIN_DIR}"
    ;;
  *)
    export PATH="${BIN_DIR}:${PATH}"
    echo "Updated current session PATH: ${BIN_DIR}"
    echo "Add this to your shell profile (.zshrc/.bashrc/.profile):"
    echo "export PATH=\"${BIN_DIR}:\$PATH\""
    ;;
esac

echo "Verify with: ${COMMAND_NAME} --help"
