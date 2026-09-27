#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
[[ -d "$IOS_BUILD_DIR/KritaIOSProbe.xcodeproj" ]] || "$IOS_SCRIPT_DIR/configure.sh"
args=()
if [[ "${KRITA_IOS_SIGN:-0}" == 1 ]]; then
    : "${KRITA_IOS_TEAM_ID:?Set KRITA_IOS_TEAM_ID for signing}"
    args+=("DEVELOPMENT_TEAM=$KRITA_IOS_TEAM_ID" -allowProvisioningUpdates)
else
    args+=(CODE_SIGNING_ALLOWED=NO)
fi
xcodebuild -project "$IOS_BUILD_DIR/KritaIOSProbe.xcodeproj" -scheme KritaIOSProbe \
    -configuration "${CONFIGURATION:-Debug}" -destination 'generic/platform=iOS' \
    -derivedDataPath "$IOS_BUILD_DIR/DerivedData" "${args[@]}" build 2>&1 | tee "$PROJECT_ROOT/logs/build-device.log"
