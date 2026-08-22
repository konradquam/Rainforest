#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
