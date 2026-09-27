#!/usr/bin/env bash
# GNU libintl for the target, not the macOS/Homebrew binary.
source "$(dirname "$0")/common.sh"
version=0.23.1
archive="$PROJECT_ROOT/.deps/downloads/gettext-$version.tar.xz"
# Autotools rejects spaces in srcdir. Build in an isolated temporary staging
# directory, then copy only the installed target artifacts into the workspace.
stage_file="$PROJECT_ROOT/.build/gettext-stage-path"
mkdir -p "$PROJECT_ROOT/.build"
if [[ -f "$stage_file" && -d "$(cat "$stage_file")" ]]; then
 stage="$(cat "$stage_file")"
else
 stage="$(mktemp -d /private/tmp/krita-ios-gettext.XXXXXX)"
 printf '%s\n' "$stage" > "$stage_file"
fi
src="$stage/gettext-$version"
bld="$stage/build"
prefix="$stage/install"
mkdir -p "$(dirname "$archive")" "$bld"
if [[ ! -f "$archive" ]]; then
 curl -fL --retry 2 "https://ftp.gnu.org/gnu/gettext/gettext-$version.tar.xz" -o "$archive.partial"
 mv "$archive.partial" "$archive"
fi
if [[ ! -d "$src" ]]; then tar -xf "$archive" -C "$stage"; fi
sdk="$(xcrun --sdk iphoneos --show-sdk-path)"
clang="$(xcrun --sdk iphoneos --find clang)"
cd "$bld"
CC="$clang" CFLAGS="-O2 -arch arm64 -isysroot $sdk -miphoneos-version-min=17.0" \
 LDFLAGS="-arch arm64 -isysroot $sdk -miphoneos-version-min=17.0" \
 "$src/gettext-runtime/configure" --host=aarch64-apple-darwin --prefix="$prefix" \
 --disable-shared --enable-static --disable-java --disable-csharp --disable-libasprintf \
 2>&1 | tee "$PROJECT_ROOT/logs/gettext-configure.log"
make -C intl -j "${BUILD_JOBS:-4}" 2>&1 | tee "$PROJECT_ROOT/logs/gettext-build.log"
make -C intl install 2>&1 | tee "$PROJECT_ROOT/logs/gettext-install.log"
mkdir -p "$PROJECT_ROOT/.deps/ios"
cp -R "$prefix/." "$PROJECT_ROOT/.deps/ios/"
shasum -a 256 "$archive" > "$PROJECT_ROOT/logs/gettext-source-sha256.txt"
