#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
version=1.87.0
archive="$PROJECT_ROOT/.deps/downloads/boost_1_87_0.tar.bz2"
mkdir -p "$PROJECT_ROOT/.deps/downloads" "$PROJECT_ROOT/.deps/src"
if [[ ! -f "$archive" ]]; then
 curl -fL --retry 2 "https://archives.boost.io/release/$version/source/boost_1_87_0.tar.bz2" -o "$archive.partial"
 mv "$archive.partial" "$archive"
fi
if [[ ! -f "$PROJECT_ROOT/.deps/src/boost_1_87_0/boost/version.hpp" ]]; then
 tar -xf "$archive" -C "$PROJECT_ROOT/.deps/src"
fi
shasum -a 256 "$archive" > "$PROJECT_ROOT/logs/boost-source-sha256.txt"
# Krita requests Boost headers only. No macOS Boost library is linked.
