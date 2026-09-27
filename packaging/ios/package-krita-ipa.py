#!/usr/bin/env python3
"""Package an app without changing its signature; verify before replacing the IPA."""

import argparse
import hashlib
import os
from pathlib import Path
import plistlib
import stat
import tempfile
import zipfile


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    app = args.app.resolve()
    output = args.output.resolve()
    require(app.is_dir(), f"Missing application bundle: {app}")
    output.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(path for path in app.rglob("*") if path.is_file())
    require(bool(files), "Application bundle is empty")
    executable_member = f"Payload/{app.name}/krita"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(temporary_name, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
            for path in files:
                archive.write(path, Path("Payload") / app.name / path.relative_to(app))

        with zipfile.ZipFile(temporary_name) as archive:
            bad_file = archive.testzip()
            require(bad_file is None, f"Corrupt IPA member: {bad_file}")
            names = archive.namelist()
            prefix = f"Payload/{app.name}/"
            require(names and all(name.startswith(prefix) for name in names),
                    "IPA contains files outside its application bundle")
            require(len(names) == len(files), "IPA file count differs from the application bundle")
            plist_name = f"{prefix}Info.plist"
            require(plist_name in names, "IPA is missing Info.plist")
            plist = plistlib.loads(archive.read(plist_name))
            executable_name = plist.get("CFBundleExecutable")
            require(executable_name == "krita", f"Unexpected IPA executable: {executable_name}")
            require(executable_member in names, "IPA is missing its main executable")
            executable_info = archive.getinfo(executable_member)
            mode = executable_info.external_attr >> 16
            require(bool(mode & stat.S_IXUSR), "IPA executable lost its executable mode")
            for path in files:
                member = f"{prefix}{path.relative_to(app).as_posix()}"
                require(digest(archive.read(member)) == digest(path.read_bytes()),
                        f"IPA content differs from application bundle: {member}")

        os.replace(temporary_name, output)
        temporary_name = None
    except (zipfile.BadZipFile, plistlib.InvalidFileException, ValueError) as error:
        fail(str(error))
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)

    ipa_bytes = output.read_bytes()
    print(f"PASS: {output}")
    print(f"Files: {len(files)}; bytes: {len(ipa_bytes)}; sha256={digest(ipa_bytes)}")


if __name__ == "__main__":
    main()
