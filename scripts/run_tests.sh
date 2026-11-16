#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-${PROJECT_ROOT}/.venv/bin/python}"

if [[ ! -x "${PYTHON}" ]]; then
    PYTHON="python"
fi

cd "${PROJECT_ROOT}"
exec "${PYTHON}" -m pytest -q tests "$@"
