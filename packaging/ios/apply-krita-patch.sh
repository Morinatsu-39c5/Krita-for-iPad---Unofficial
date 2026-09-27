#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
src="$PROJECT_ROOT/upstream/krita"
revision=3a9b5ef03f8312b6f630fc5d475e1692598e8719
[[ "$(git -C "$src" rev-parse HEAD)" == "$revision" ]] || { echo 'Unexpected Krita base revision'; exit 1; }
patch="$PROJECT_ROOT/patches/ios/krita-ipados.patch"
if git -C "$src" apply --check "$patch"; then
 git -C "$src" apply "$patch"
elif git -C "$src" apply --reverse --check "$patch"; then
 echo 'Krita iPadOS patch is already applied'
else
 echo 'Patch conflicts with local edits; nothing changed' >&2
 exit 1
fi
