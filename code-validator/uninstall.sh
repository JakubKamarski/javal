#!/usr/bin/env bash
set -euo pipefail

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

if [[ -L "${COMMAND_PATH}" || -f "${COMMAND_PATH}" ]]; then
  rm -f "${COMMAND_PATH}"
  echo "Removed: ${COMMAND_PATH}"
else
  echo "No command found at: ${COMMAND_PATH}"
fi

if [[ -d "${BIN_DIR}" ]] && [[ -z "$(ls -A "${BIN_DIR}")" ]]; then
  rmdir "${BIN_DIR}" || true
fi

echo "Uninstalled command: ${COMMAND_NAME}"
echo "If you added PATH manually, you can remove:"
echo "export PATH=\"${BIN_DIR}:\$PATH\""
