#!/usr/bin/env python3
"""Record literal CMake package declarations; does not claim a resolved dependency graph."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[2]
source = root / 'upstream/krita'
rows = []
for path in sorted(source.rglob('*')):
    if path.name != 'CMakeLists.txt' and path.suffix != '.cmake':
        continue
    text = path.read_text(errors='replace')
    for match in re.finditer(r'(?im)^\s*(?:find_package|find_dependency)\s*\(', text):
        end = text.find(')', match.end())
        declaration = ' '.join(text[match.start():end + 1].split())
        line = text.count('\n', 0, match.start()) + 1
        rows.append(f'| `{path.relative_to(source)}:{line}` | `{declaration}` |')
output = root / 'docs/ios/dependency-declarations.md'
output.write_text('# Krita CMake dependency declarations\n\nSource: `3a9b5ef03f8312b6f630fc5d475e1692598e8719`.\n\nStatic inventory, including conditional/optional/test/vendor declarations. Versions and variables remain literal; this is not a successful iOS resolution. Classification is in dependencies.md.\n\n| Source | Declaration |\n| --- | --- |\n' + '\n'.join(rows) + '\n')
print(f'{len(rows)} declarations -> {output}')
