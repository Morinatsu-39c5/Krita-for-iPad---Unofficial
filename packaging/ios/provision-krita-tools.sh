#!/usr/bin/env bash
# Host tools and official Qt modules required by the current Krita Qt 6 source.
source "$(dirname "$0")/common.sh"
"$PROJECT_ROOT/.venv/bin/python" -m pip install meson==1.10.1 pkgconf==2.5.1.post2
for spec in 'desktop clang_64' 'ios ios'; do
 read -r target arch <<< "$spec"
 modules=(qtsvg qt5compat qtshadertools)
 if [[ "$target" == desktop ]]; then modules+=(qttools); fi
 "$PROJECT_ROOT/.venv/bin/aqt" install-qt mac "$target" "$QT_VERSION" "$arch" \
   -O "$PROJECT_ROOT/.qt" --archives qtdeclarative --modules "${modules[@]}"
done
