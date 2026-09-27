#!/usr/bin/env bash
# Incrementally build, sign, install and launch the full Krita app on one iPad.
source "$(dirname "$0")/common.sh"

KRITA_BUILD_DIR="${KRITA_BUILD_DIR:-$PROJECT_ROOT/.build/krita-ios-xcode}"
KRITA_CONFIGURATION="${KRITA_CONFIGURATION:-Release}"
KRITA_IOS_BUNDLE_ID="${KRITA_IOS_BUNDLE_ID:-org.example.krita}"

: "${KRITA_IOS_TEAM_ID:?Set KRITA_IOS_TEAM_ID to the Apple Development Team ID}"
: "${KRITA_IOS_DEVICE_ID:?Set KRITA_IOS_DEVICE_ID to the connected iPad identifier}"

export KRITA_BUILD_DIR KRITA_IOS_TEAM_ID KRITA_IOS_BUNDLE_ID

project="$KRITA_BUILD_DIR/krita.xcodeproj"
app="$KRITA_BUILD_DIR/bin/$KRITA_CONFIGURATION/krita.app"
log="$PROJECT_ROOT/logs/krita-xcode-signed-device.log"

[[ -d "$project" ]] || {
    echo "Missing Xcode project: $project" >&2
    echo "Generate it first with packaging/ios/configure-krita-xcode.sh" >&2
    exit 1
}

echo "Close Xcode before running this command so it does not lock the build database."

# Refresh the generated project without deleting incremental build products.
# KritaIOS.cmake enables signing only for the final application target; passing
# signing settings to xcodebuild would incorrectly apply them to every static
# library and plugin target.
"$IOS_SCRIPT_DIR/configure-krita-xcode.sh"

xcodebuild -project "$project" -scheme krita \
    -configuration "$KRITA_CONFIGURATION" \
    -sdk iphoneos \
    -destination "id=$KRITA_IOS_DEVICE_ID" \
    -allowProvisioningUpdates \
    build 2>&1 | tee "$log"

[[ -d "$app" ]] || {
    echo "Signed application is missing: $app" >&2
    exit 1
}

if ! verify_output="$(codesign --verify --deep --strict "$app" 2>&1)"; then
    if [[ "$verify_output" != *CSSMERR_TP_NOT_TRUSTED* ]]; then
        echo "$verify_output" >&2
        exit 1
    fi
    echo "Warning: macOS did not trust the local development certificate chain; continuing with device installation." >&2
fi
codesign -dvvv "$app" 2>&1
xcrun devicectl device install app --device "$KRITA_IOS_DEVICE_ID" "$app"

if [[ "${KRITA_IOS_LAUNCH:-1}" == 1 ]]; then
    xcrun devicectl device process launch \
        --device "$KRITA_IOS_DEVICE_ID" "$KRITA_IOS_BUNDLE_ID"
fi

echo "Installed app: $app"
