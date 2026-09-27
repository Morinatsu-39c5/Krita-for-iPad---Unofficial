#!/usr/bin/env python3
"""Reject host or simulator objects accidentally installed into the iOS prefix."""
from pathlib import Path
import argparse
import re
import subprocess
root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path, default=root / '.deps/ios/lib')
parser.add_argument('--report', type=Path, default=root / 'docs/ios/target-libraries.txt')
args = parser.parse_args()
libs = sorted(args.directory.glob('*.a'))
if not libs:
    raise SystemExit('No target libraries found')
report = []
for lib in libs:
    arch = subprocess.check_output(['xcrun', 'lipo', '-archs', str(lib)], text=True).strip()
    load = subprocess.check_output(['xcrun', 'otool', '-l', str(lib)], text=True)
    platforms = set(re.findall(r'^\s*platform\s+(\S+)', load, re.M))
    if arch != 'arm64' or platforms != {'2'}:
        raise SystemExit(f'Invalid target library: {lib.name}, arch={arch}, platforms={platforms}')
    report.append(f'{lib.name}: arm64 / platform 2 (iOS device)')
output = args.report
output.write_text('\n'.join(report) + '\n')
print('\n'.join(report))
