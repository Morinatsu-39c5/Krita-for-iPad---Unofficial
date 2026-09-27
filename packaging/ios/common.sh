#!/usr/bin/env bash
set -euo pipefail
IOS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$IOS_SCRIPT_DIR/../.." && pwd)"
QT_VERSION="${QT_VERSION:-6.10.3}"
QT_IOS_PREFIX="${QT_IOS_PREFIX:-$PROJECT_ROOT/.qt/$QT_VERSION/ios}"
QT_HOST_PATH="${QT_HOST_PATH:-$PROJECT_ROOT/.qt/$QT_VERSION/macos}"
IOS_BUILD_DIR="${IOS_BUILD_DIR:-$PROJECT_ROOT/.build/ios-probe}"
mkdir -p "$PROJECT_ROOT/logs"
