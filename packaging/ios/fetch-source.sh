#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
revision=3a9b5ef03f8312b6f630fc5d475e1692598e8719
source_dir="$PROJECT_ROOT/upstream/krita"
if [[ -e "$source_dir" ]]; then
    [[ "$(git -C "$source_dir" rev-parse HEAD)" == "$revision" ]] || { echo 'Existing checkout differs; not overwriting' >&2; exit 1; }
else
    git init "$source_dir"
    git -C "$source_dir" remote add origin https://github.com/KDE/krita.git
    git -C "$source_dir" fetch --depth 1 origin "$revision"
    git -C "$source_dir" checkout --detach FETCH_HEAD
fi
