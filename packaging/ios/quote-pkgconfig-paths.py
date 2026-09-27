#!/usr/bin/env python3
"""Quote variable-based include/library flags in target .pc files for spaced paths."""
import re
import sys
from pathlib import Path
for path in Path(sys.argv[1]).glob('*.pc'):
    lines = path.read_text().splitlines(keepends=True)
    escaped_values = any('\\ ' in line and '=' in line for line in lines)
    for i, line in enumerate(lines):
        if line.startswith(('Cflags:', 'Libs:', 'Libs.private:')):
            if escaped_values:
                lines[i] = re.sub(r'"((?:-I|-L)\$\{[^}]+\}[^"]*)"', r'\1', line)
                continue
            lines[i] = re.sub(r'(?<![\w"\'])((?:-I|-L)\$\{[^}]+\}[^\s"\']*)', r'"\1"', line)
    path.write_text(''.join(lines))
