#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS and Xcode are required' >&2; exit 1; }
[[ -f "$QT_IOS_PREFIX/lib/cmake/Qt6/qt.toolchain.cmake" ]] || { echo "Missing Qt iOS kit: $QT_IOS_PREFIX. Run packaging/ios/build-deps.sh" >&2; exit 1; }
cmake -S "$IOS_SCRIPT_DIR/probe" -B "$IOS_BUILD_DIR" -G Xcode \
    -DCMAKE_TOOLCHAIN_FILE="$QT_IOS_PREFIX/lib/cmake/Qt6/qt.toolchain.cmake" \
    -DQT_HOST_PATH="$QT_HOST_PATH" -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 \
    -DCMAKE_OSX_DEPLOYMENT_TARGET="${KRITA_IOS_MIN_VERSION:-17.0}" \
    -DKRITA_IOS_BUNDLE_ID="${KRITA_IOS_BUNDLE_ID:-org.example.krita.probe}" \
    -DKRITA_IOS_TEAM_ID="${KRITA_IOS_TEAM_ID:-}" "$@" 2>&1 | tee "$PROJECT_ROOT/logs/configure-ios.log"
