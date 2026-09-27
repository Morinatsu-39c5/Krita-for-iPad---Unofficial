#!/usr/bin/env python3
"""Generate an opaque geometric probe icon using only Python's standard library."""
import struct
import zlib
from pathlib import Path
size = 1024
raw = bytearray()
for y in range(size):
    raw.append(0)
    for x in range(size):
        # Letter P on a solid background distinguishes the test app from Krita.
        letter = (260 <= x < 370 and 220 <= y < 810) or (370 <= x < 690 and (220 <= y < 330 or 490 <= y < 600)) or (650 <= x < 760 and 270 <= y < 550)
        raw.extend((245, 248, 255) if letter else (28, 73, 111))
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', size, size, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
Path(__file__).with_name('Assets.xcassets').joinpath('AppIcon.appiconset', 'Probe.png').write_bytes(png)
