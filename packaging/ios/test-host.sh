#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
cmake -S "$IOS_SCRIPT_DIR/probe" -B "$PROJECT_ROOT/.build/macos-probe" -G Ninja \
    -DCMAKE_PREFIX_PATH="$QT_HOST_PATH" -DCMAKE_BUILD_TYPE=Debug
cmake --build "$PROJECT_ROOT/.build/macos-probe" --parallel 4
QT_QPA_PLATFORM=offscreen "$PROJECT_ROOT/.build/macos-probe/KritaIOSProbe.app/Contents/MacOS/KritaIOSProbe" --self-test
