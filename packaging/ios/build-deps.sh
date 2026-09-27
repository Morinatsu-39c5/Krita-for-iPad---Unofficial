#!/usr/bin/env bash
# Phase 1 only: provision official Qt binaries, not the full Krita dependency graph.
source "$(dirname "$0")/common.sh"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS and Xcode are required' >&2; exit 1; }
xcrun --sdk iphoneos --show-sdk-version
if [[ ! -x "$PROJECT_ROOT/.venv/bin/aqt" ]]; then
    python3 -m venv "$PROJECT_ROOT/.venv"
    "$PROJECT_ROOT/.venv/bin/python" -m pip install 'aqtinstall==3.3.0'
fi
for target in desktop ios; do
    if [[ "$target" == desktop ]]; then arch=clang_64; prefix="$QT_HOST_PATH"; else arch=ios; prefix="$QT_IOS_PREFIX"; fi
    if [[ ! -f "$prefix/lib/cmake/Qt6/Qt6Config.cmake" ]]; then
        "$PROJECT_ROOT/.venv/bin/aqt" install-qt mac "$target" "$QT_VERSION" "$arch" \
            -O "$PROJECT_ROOT/.qt" --archives qtbase 2>&1 | tee "$PROJECT_ROOT/logs/qt-$target.log"
    fi
done
