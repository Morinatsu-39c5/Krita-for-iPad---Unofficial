#!/usr/bin/env bash
# Build one named, pinned prerequisite at a time; no all-dependencies fallback.
source "$(dirname "$0")/common.sh"
name="${1:?Usage: build-krita-deps.sh PACKAGE}"
shift
case "$name" in
 freetype) repo=freetype/freetype; revision=VER-2-14-3; platform=ios ;;
 harfbuzz) repo=harfbuzz/harfbuzz; revision=12.3.2; platform=ios ;;
 unibreak) repo=adah1972/libunibreak; revision=libunibreak_7_0; platform=ios ;;
 gsl) repo=ampl/gsl; revision=fb0cfbc82b5e9e4d22444efce9241924f4aefb83; platform=ios ;;
 xsimd) repo=xtensor-stack/xsimd; revision=14.1.0; platform=ios ;;
 quazip) repo=stachenov/quazip; revision=v1.4; platform=ios ;;
 brotli) repo=google/brotli; revision=v1.2.0; platform=ios ;;
 eigen) repo=https://gitlab.com/libeigen/eigen.git; revision=5.0.1; platform=ios ;;
 expat) repo=libexpat/libexpat; revision=R_2_7_5; platform=ios ;;
 exiv2) repo=Exiv2/exiv2; revision=v0.28.8; platform=ios ;;
 lcms2) repo=mm2/Little-CMS; revision=lcms2.19; platform=ios ;;
 jpeg) repo=libjpeg-turbo/libjpeg-turbo; revision=3.1.4.1; platform=ios ;;
 immer) repo=arximboldi/immer; revision=v0.9.1; platform=ios ;;
 zug) repo=arximboldi/zug; revision=v0.1.2; platform=ios ;;
 lager) repo=dimula73/lager; revision=0b6ab3e0e880bc36be5da4984d768fde03b7cf19; platform=ios ;;
 png) repo=pnggroup/libpng; revision=v1.6.50; platform=ios ;;
 host-kconfig) repo=KDE/kconfig; revision=v6.18.0; platform=host ;;
 ecm) repo=KDE/extra-cmake-modules; revision=v6.18.0; platform=host ;;
 kcodecs|kconfig|kwidgetsaddons|kcompletion|kcoreaddons|kguiaddons|ki18n|kitemviews|kcolorscheme)
    repo="KDE/$name"; revision=v6.18.0; platform=ios ;;
 *) echo "Unknown prerequisite: $name" >&2; exit 2 ;;
esac
if [[ "$repo" == https://* ]]; then repo_url="$repo"; else repo_url="https://github.com/$repo.git"; fi
# Patches are tied to immutable commits, even if the readable version tag moves.
revision="$(python3 - "$PROJECT_ROOT/patches/ios/baselines.json" "$name" "$revision" <<'PY'
import json
import sys
from pathlib import Path
baseline = json.loads(Path(sys.argv[1]).read_text())
entry = baseline["patchedDependencies"].get(sys.argv[2])
print(entry["revision"] if entry else sys.argv[3])
PY
)"
src="$PROJECT_ROOT/.deps/src/$name"
bld="$PROJECT_ROOT/.build/deps-$platform/$name"
prefix="$PROJECT_ROOT/.deps/$platform"
if [[ ! -d "$src/.git" ]]; then
 git init "$src"
 git -C "$src" remote add origin "$repo_url"
fi
if ! git -C "$src" rev-parse --verify HEAD >/dev/null 2>&1; then
 git -C "$src" fetch --depth 1 origin "$revision"
 git -C "$src" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$src" rev-parse HEAD)" != "$(git -C "$src" rev-parse --verify "${revision}^{commit}" 2>/dev/null || git -C "$src" rev-parse "FETCH_HEAD^{commit}")" ]]; then
 echo "Unexpected source revision for $name; not changing the existing checkout" >&2; exit 1
fi
if [[ -f "$PROJECT_ROOT/patches/ios/$name-no-process.patch" ]]; then
 patch="$PROJECT_ROOT/patches/ios/$name-no-process.patch"
 if git -C "$src" apply --check "$patch" 2>/dev/null; then
  git -C "$src" apply "$patch"
 elif ! git -C "$src" apply --reverse --check "$patch" 2>/dev/null; then
  echo 'Dependency patch conflicts with local edits' >&2; exit 1
 fi
fi
for patch in "$PROJECT_ROOT/patches/ios/dependencies/$name"/*.patch; do
 [[ -f "$patch" ]] || continue
 if git -C "$src" apply --check "$patch" 2>/dev/null; then
  git -C "$src" apply "$patch"
 elif ! git -C "$src" apply --reverse --check "$patch" 2>/dev/null; then
  echo "Patch conflict: $patch" >&2; exit 1
 fi
done
args=(-DECM_DIR="$PROJECT_ROOT/.deps/host/share/ECM/cmake" -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release
      -DCMAKE_INSTALL_PREFIX="$prefix" -DBUILD_QCH=OFF)
if [[ "$platform" == host ]]; then args+=(-DCMAKE_PREFIX_PATH="$PROJECT_ROOT/.deps/host;$QT_HOST_PATH"); fi
if [[ "$platform" == ios ]]; then
 args+=(-DCMAKE_TOOLCHAIN_FILE="$QT_IOS_PREFIX/lib/cmake/Qt6/qt.toolchain.cmake"
        -DECM_DIR="$PROJECT_ROOT/.deps/host/share/ECM/cmake" -DQT_HOST_PATH="$QT_HOST_PATH" -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_SYSTEM_PROCESSOR=arm64
        -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=17.0
        -DCMAKE_FIND_ROOT_PATH="$PROJECT_ROOT/.deps/ios" -DKF6_HOST_TOOLING="$PROJECT_ROOT/.deps/host/lib/cmake" -DKF_IGNORE_PLATFORM_CHECK=TRUE -DCMAKE_PREFIX_PATH="$PROJECT_ROOT/.deps/ios;$PROJECT_ROOT/.deps/host;$QT_IOS_PREFIX"
        -DCMAKE_DISABLE_FIND_PACKAGE_Qt6Qml=TRUE
        -DQt6LinguistTools_DIR="$QT_HOST_PATH/lib/cmake/Qt6LinguistTools")
fi
if [[ "$name" == immer || "$name" == zug || "$name" == lager ]]; then
 args+=("-D${name}_BUILD_TESTS=OFF" "-D${name}_BUILD_EXAMPLES=OFF" "-D${name}_BUILD_DOCS=OFF")
fi
if [[ "$name" == lager ]]; then args+=(-Dlager_BUILD_DEBUGGER_EXAMPLES=OFF); fi
if [[ "$name" == png ]]; then args+=(-DPNG_FRAMEWORK=OFF -DPNG_SHARED=OFF -DPNG_TESTS=OFF -DPNG_TOOLS=OFF); fi
if [[ "$name" == *kconfig ]]; then args+=(-DKCONFIG_USE_QML=OFF); fi
if [[ "$name" == ki18n ]]; then args+=(-DBUILD_WITH_QML=OFF); fi
if [[ "$name" == kcoreaddons ]]; then args+=(-DKCOREADDONS_USE_QML=OFF); fi
cmake_src="$src"
case "$name" in
 freetype) args+=(-DFT_DISABLE_BZIP2=ON -DFT_DISABLE_BROTLI=ON -DFT_REQUIRE_PNG=ON -DFT_DISABLE_HARFBUZZ=ON) ;;
 harfbuzz) args+=(-DHB_HAVE_FREETYPE=ON -DHB_HAVE_GLIB=OFF -DHB_HAVE_ICU=OFF -DHB_BUILD_UTILS=OFF) ;;
 gsl) args+=(-DNO_AMPL_BINDINGS=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5) ;;
 quazip) args+=(-DQUAZIP_BZIP2=OFF -DQUAZIP_QT_MAJOR_VERSION=6 -DQUAZIP_ENABLE_TESTS=OFF) ;;
 brotli) args+=(-DBROTLI_BUILD_TOOLS=OFF -DBROTLI_DISABLE_TESTS=ON) ;;
 eigen) args+=(-DEIGEN_BUILD_BLAS=OFF -DEIGEN_BUILD_LAPACK=OFF) ;;
 expat) cmake_src="$src/expat"; args+=(-DEXPAT_BUILD_TOOLS=OFF -DEXPAT_BUILD_EXAMPLES=OFF -DEXPAT_BUILD_TESTS=OFF -DEXPAT_SHARED_LIBS=OFF) ;;
 exiv2) args+=(-DEXIV2_BUILD_SAMPLES=OFF -DEXIV2_ENABLE_NLS=OFF -DEXIV2_BUILD_EXIV2_COMMAND=OFF -DEXIV2_ENABLE_INIH=OFF -DEXIV2_BUILD_UNIT_TESTS=OFF -DEXIV2_BUILD_FUZZ_TESTS=OFF) ;;
 lcms2) args+=(-DLCMS2_BUILD_TESTS=OFF -DLCMS2_BUILD_TOOLS=OFF -DLCMS2_BUILD_SHARED=OFF -DLCMS2_BUILD_STATIC=ON -DLCMS2_WITH_FASTFLOAT=ON) ;;
 jpeg) args+=(-DENABLE_SHARED=OFF -DENABLE_STATIC=ON -DWITH_TOOLS=OFF) ;;
esac
cmake -S "$cmake_src" -B "$bld" -G Ninja "${args[@]}" "$@" 2>&1 | tee "$PROJECT_ROOT/logs/deps-$name-configure.log"
cmake --build "$bld" --parallel "${BUILD_JOBS:-4}" 2>&1 | tee "$PROJECT_ROOT/logs/deps-$name-build.log"
cmake --install "$bld" 2>&1 | tee "$PROJECT_ROOT/logs/deps-$name-install.log"
git -C "$src" rev-parse HEAD > "$PROJECT_ROOT/logs/deps-$name-revision.txt"

python3 "$IOS_SCRIPT_DIR/quote-pkgconfig-paths.py" "$prefix/lib/pkgconfig"
