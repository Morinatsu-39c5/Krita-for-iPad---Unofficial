#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
export KRITA_BUILD_DIR="${KRITA_BUILD_DIR:-$PROJECT_ROOT/.build/krita-ios-xcode}"
export KRITA_GENERATOR=Xcode
exec "$IOS_SCRIPT_DIR/configure-krita.sh" \
 -DCMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED=NO \
 -DCMAKE_XCODE_ATTRIBUTE_SUPPORTED_PLATFORMS=iphoneos \
 -DCMAKE_XCODE_ATTRIBUTE_SUPPORTS_MACCATALYST=NO \
 "$@"
