#!/usr/bin/env bash
# Clean-install smoke test: verifies that `pip install scikit-video` in a
# fresh venv brings in every runtime dependency the package needs at import
# time (historically this caught hidden requirements, e.g. the undeclared
# cv2 dependency before v1.1.12; cv2 was removed entirely in 1.2.1).
#
# Run this before tagging a release. If it exits non-zero, do not tag.
#
# Usage:
#   ./scripts/smoke_clean_install.sh                  # installs the current checkout (`pip install .`)
#   ./scripts/smoke_clean_install.sh scikit-video     # installs from PyPI (post-release verification)
#
# Requires: python3, the `venv` stdlib module, network access if installing from PyPI.

set -euo pipefail

TARGET="${1:-.}"
VENV_DIR="$(mktemp -d -t skvideo-smoke-XXXXXX)"
trap 'rm -rf "$VENV_DIR"' EXIT

echo "Creating fresh venv at $VENV_DIR"
python3 -m venv "$VENV_DIR"

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade --quiet pip
python -m pip install --quiet "$TARGET"

echo "--- Installed packages ---"
python -m pip list

echo "--- Import smoke test ---"
python - <<'PY'
import skvideo
import skvideo.io
import skvideo.motion
import skvideo.measure  # historically the import with hidden deps
import skvideo.datasets
import skvideo.utils
print("OK skvideo", skvideo.__version__)
PY

echo "Clean-install smoke test PASSED for target: $TARGET"
