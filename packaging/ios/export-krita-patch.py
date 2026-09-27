#!/usr/bin/env python3
"""Atomically export the current Krita port without staging or committing."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "upstream/krita"
DEFAULT_OUTPUT = PROJECT_ROOT / "patches/ios/krita-ipados.patch"
DEFAULT_HEAD = "3a9b5ef03f8312b6f630fc5d475e1692598e8719"


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(args, cwd=cwd, capture_output=True)
    if check and result.returncode:
        detail = result.stderr.decode(errors="replace").strip()
        raise SystemExit(detail or f"Command failed ({result.returncode}): {' '.join(args)}")
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_patch(source: Path) -> bytes:
    diff = run("git", "diff", "--binary", "HEAD", "--", cwd=source).stdout
    names = run(
        "git", "ls-files", "--others", "--exclude-standard", "-z", cwd=source
    ).stdout.split(b"\0")
    for raw_name in names:
        if not raw_name:
            continue
        name = os.fsdecode(raw_name)
        result = run(
            "git", "diff", "--no-index", "--binary", "--", "/dev/null", name,
            cwd=source, check=False,
        )
        if result.returncode not in (0, 1):
            detail = result.stderr.decode(errors="replace").strip()
            raise SystemExit(detail or f"Could not export untracked file: {name}")
        diff += result.stdout
    return diff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-head", default=DEFAULT_HEAD)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if not (source / ".git").exists():
        raise SystemExit(f"Not a Git checkout: {source}")
    actual_head = run("git", "rev-parse", "HEAD", cwd=source).stdout.decode().strip()
    if args.expected_head and actual_head != args.expected_head:
        raise SystemExit(
            f"Unexpected Krita HEAD: {actual_head}; expected {args.expected_head}"
        )

    diff = build_patch(source)
    if not diff and not args.allow_empty:
        raise SystemExit("Refusing to replace the port patch with an empty file")

    output.parent.mkdir(parents=True, exist_ok=True)
    previous = output.read_bytes() if output.exists() else b""
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output.parent, prefix=f".{output.name}.", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(diff)
            temporary.flush()
            os.fsync(temporary.fileno())

        if diff:
            check = run(
                "git", "apply", "--reverse", "--check", temporary_name,
                cwd=source, check=False,
            )
            if check.returncode:
                detail = check.stderr.decode(errors="replace").strip()
                raise SystemExit(f"Generated patch does not reverse-apply: {detail}")

        os.replace(temporary_name, output)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)

    print(f"Patch: {output}")
    print(f"HEAD: {actual_head}")
    print(f"Previous: {len(previous)} bytes sha256={sha256(previous)}")
    print(f"Current: {len(diff)} bytes sha256={sha256(diff)}")


if __name__ == "__main__":
    main()
