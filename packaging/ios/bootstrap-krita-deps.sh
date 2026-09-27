#!/usr/bin/env bash
# Prepare the pinned source, Qt kits and dependencies; stop on the first failure.
source "$(dirname "$0")/common.sh"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS and Xcode are required' >&2; exit 1; }
for command in git python3 cmake ninja curl xcrun msgfmt msgmerge pkg-config; do
    command -v "$command" >/dev/null || { echo "Missing tool: $command" >&2; exit 1; }
done
xcrun --sdk iphoneos --show-sdk-version

"$IOS_SCRIPT_DIR/fetch-source.sh"
"$IOS_SCRIPT_DIR/apply-krita-patch.sh"
"$IOS_SCRIPT_DIR/build-deps.sh"
"$IOS_SCRIPT_DIR/provision-krita-tools.sh"
"$IOS_SCRIPT_DIR/build-krita-deps.sh" ecm
"$IOS_SCRIPT_DIR/build-krita-deps.sh" host-kconfig
"$IOS_SCRIPT_DIR/build-gettext.sh"

for package in kconfig kwidgetsaddons kcoreaddons kcodecs kcompletion kguiaddons kitemviews ki18n kcolorscheme; do
    echo "Building prerequisite: $package"
    if [[ "$package" == ki18n ]]; then
        "$IOS_SCRIPT_DIR/build-krita-deps.sh" "$package" -U HAVE_NL_MSG_CAT_CNTR
    else
        "$IOS_SCRIPT_DIR/build-krita-deps.sh" "$package"
    fi
done
for package in png expat brotli jpeg lcms2 exiv2 immer zug lager eigen; do
    echo "Building prerequisite: $package"
    "$IOS_SCRIPT_DIR/build-krita-deps.sh" "$package"
done
"$IOS_SCRIPT_DIR/fetch-boost.sh"
for package in freetype harfbuzz unibreak; do
    "$IOS_SCRIPT_DIR/build-krita-deps.sh" "$package"
done
"$IOS_SCRIPT_DIR/build-fontconfig.sh"
"$IOS_SCRIPT_DIR/build-fribidi.sh"
for package in quazip xsimd gsl; do
    "$IOS_SCRIPT_DIR/build-krita-deps.sh" "$package"
done
echo 'Source and dependencies prepared. Generate the Krita Xcode project next.'
