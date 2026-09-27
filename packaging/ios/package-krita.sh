#!/usr/bin/env bash
# Package the existing CMake install layout into the unsigned iPad application.
source "$(dirname "$0")/common.sh"
KRITA_BUILD_DIR="${KRITA_BUILD_DIR:-$PROJECT_ROOT/.build/krita-ios}"
stage="$PROJECT_ROOT/.build/krita-ios-install"
app="$stage/krita.app"
cmake --install "$KRITA_BUILD_DIR" --config "${KRITA_BUILD_CONFIG:-Release}" --prefix "$stage" 2>&1 | tee "$PROJECT_ROOT/logs/krita-install.log"
[[ -x "$app/krita" ]] || { echo 'Krita executable is missing'; exit 1; }
[[ -d "$stage/share/krita" ]] || { echo 'Installed Krita resources are missing'; exit 1; }
mkdir -p "$app/share"
# Dereference data symlinks. No static archives or external code are copied.
cp -RL "$stage/share/." "$app/share/"
plutil -lint "$app/Info.plist"
xcrun lipo -archs "$app/krita"
xcrun otool -L "$app/krita" | tee "$PROJECT_ROOT/logs/krita-app-linked-libraries.txt"
python3 "$IOS_SCRIPT_DIR/verify-krita-app.py" "$app" --build-dir "$KRITA_BUILD_DIR" \
 | tee "$PROJECT_ROOT/logs/krita-app-validation.txt"
python3 "$IOS_SCRIPT_DIR/package-krita-ipa.py" "$app" \
 "$PROJECT_ROOT/.build/Krita-iPadOS-unsigned.ipa" \
 | tee "$PROJECT_ROOT/logs/krita-ipa-validation.txt"
printf 'Unsigned app: %s\n' "$app"
