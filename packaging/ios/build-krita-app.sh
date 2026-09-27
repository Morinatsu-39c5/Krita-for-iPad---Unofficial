#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
KRITA_BUILD_DIR="${KRITA_BUILD_DIR:-$PROJECT_ROOT/.build/krita-ios}"
cmake --build "$KRITA_BUILD_DIR" --config "${KRITA_BUILD_CONFIG:-Release}" --target krita kritalibkis kritaexifcommon \
 --parallel "${BUILD_JOBS:-4}" 2>&1 | tee "$PROJECT_ROOT/logs/krita-app-build.log"
