#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
archive="$PROJECT_ROOT/.deps/downloads/fontconfig-2.16.0.tar.xz"
src="$PROJECT_ROOT/.deps/src/fontconfig-2.16.0"
bld="$PROJECT_ROOT/.build/deps-ios/fontconfig"
prefix="$PROJECT_ROOT/.deps/ios"
if [[ ! -f "$archive" ]]; then
 curl -fL --retry 2 https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.16.0.tar.xz -o "$archive"
fi
printf '%s  %s\n' 6a33dc555cc9ba8b10caf7695878ef134eeb36d0af366041f639b1da9b6ed220 "$archive" | shasum -a 256 -c -
if [[ ! -d "$src" ]]; then tar -xf "$archive" -C "$PROJECT_ROOT/.deps/src"; fi
export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
export PKG_CONFIG_PATH="$prefix/lib/pkgconfig:$prefix/share/pkgconfig"
export PKG_CONFIG_LIBDIR="$prefix/lib/pkgconfig:$prefix/share/pkgconfig"
pkgconf="$("$PROJECT_ROOT/.venv/bin/python" -c 'import pkgconf,pathlib; print(pathlib.Path(pkgconf.__path__[0])/".bin/pkgconf")')"
sdk="$(xcrun --sdk iphoneos --show-sdk-path)"
mkdir -p "$bld" "$PROJECT_ROOT/.build/ios-sdk-pkgconfig"
# The SDK supplies libz but no pkg-config metadata. Keep this metadata separate
# from source-built dependencies and derive the version from the selected SDK.
zversion="$(sed -n 's/^#define ZLIB_VERSION "\(.*\)"/\1/p' "$sdk/usr/include/zlib.h")"
cat > "$PROJECT_ROOT/.build/ios-sdk-pkgconfig/zlib.pc" <<ZLIB
Name: zlib
Description: zlib from the selected iPhoneOS SDK
Version: $zversion
Libs: -lz
ZLIB
export PKG_CONFIG_LIBDIR="$PKG_CONFIG_LIBDIR:$PROJECT_ROOT/.build/ios-sdk-pkgconfig"
export PKG_CONFIG_PATH="$PKG_CONFIG_LIBDIR"
cat > "$bld/ios.ini" <<CROSS
[binaries]
c = '$(xcrun --sdk iphoneos --find clang)'
cpp = '$(xcrun --sdk iphoneos --find clang++)'
ar = '$(xcrun --find ar)'
strip = '$(xcrun --find strip)'
pkg-config = '$pkgconf'
[host_machine]
system = 'darwin'
cpu_family = 'aarch64'
cpu = 'arm64'
endian = 'little'
[properties]
needs_exe_wrapper = true
[built-in options]
c_args = ['-arch', 'arm64', '-isysroot', '$sdk', '-miphoneos-version-min=17.0']
c_link_args = ['-arch', 'arm64', '-isysroot', '$sdk', '-miphoneos-version-min=17.0']
pkg_config_path = ['$prefix/lib/pkgconfig', '$prefix/share/pkgconfig']
CROSS
python3 "$IOS_SCRIPT_DIR/quote-pkgconfig-paths.py" "$prefix/lib/pkgconfig"
meson setup --clearcache --reconfigure "$bld" "$src" --cross-file "$bld/ios.ini" --prefix "$prefix" --libdir lib --default-library static --buildtype release --wrap-mode=nofallback -Ddoc=disabled -Dcache-build=disabled -Dtests=disabled -Dtools=disabled -Dnls=disabled -Dxml-backend=expat 2>&1 | tee "$PROJECT_ROOT/logs/fontconfig-configure.log"
meson compile -C "$bld" -j "${BUILD_JOBS:-4}" 2>&1 | tee "$PROJECT_ROOT/logs/fontconfig-build.log"
meson install -C "$bld" 2>&1 | tee "$PROJECT_ROOT/logs/fontconfig-install.log"
