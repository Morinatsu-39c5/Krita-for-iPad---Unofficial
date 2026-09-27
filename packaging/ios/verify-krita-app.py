#!/usr/bin/env python3
"""Validate an iPad device bundle; this does not replace a device launch test."""

import argparse
import gettext
import json
from pathlib import Path
import plistlib
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def command(*args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode and not allow_failure:
        fail(result.stderr.strip() or result.stdout.strip() or " ".join(args))
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_build_type(build_dir: Path) -> tuple[str, str]:
    cache = build_dir / "CMakeCache.txt"
    require(cache.is_file(), f"Missing CMake cache: {cache}")
    cache_text = cache.read_text(errors="replace")
    match = re.search(r"^CMAKE_BUILD_TYPE:STRING=(.*)$", cache_text, re.MULTILINE)
    build_type = match.group(1) if match and match.group(1) else "multi-config"
    ninja = build_dir / "build.ninja"
    evidence = ninja.read_text(errors="replace") if ninja.is_file() else ""
    if build_type.lower() == "release":
        require("_debug" not in evidence, "Release build graph references Qt debug libraries")
        require("DNDEBUG" in evidence, "Release build graph does not define NDEBUG")
        require(bool(re.search(r"(?:^|\s)-O(?:[0-3s]|fast)(?:\s|$)", evidence)),
                "Release build graph has no optimization flag")
    return build_type, evidence


def verify_qrc(executable: Path, build_dir: Path) -> int:
    manifest = build_dir / "krita/ios-static-resources.tsv"
    require(manifest.is_file(), f"Missing static resource manifest: {manifest}")
    symbols = command("xcrun", "nm", "-a", str(executable)).stdout
    count = 0
    for line_number, line in enumerate(manifest.read_text().splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        require(len(fields) == 3, f"Invalid resource manifest line {line_number}: {line}")
        name, sentinel, qrc_name = fields
        require(f"qInitResources_{name}" in symbols,
                f"Static resource initializer is missing: {name}")
        qrc_path = Path(qrc_name)
        require(qrc_path.is_file(), f"Registered qrc source is missing: {qrc_path}")
        try:
            qrc_root = ET.parse(qrc_path).getroot()
        except (ET.ParseError, OSError) as error:
            fail(f"Cannot parse registered qrc source {qrc_path}: {error}")
        resources = set()
        for qresource in qrc_root.findall("qresource"):
            prefix = qresource.get("prefix", "/").strip("/")
            for file_element in qresource.findall("file"):
                relative = file_element.get("alias") or (file_element.text or "").strip()
                if relative:
                    path = "/".join(part for part in (prefix, relative) if part)
                    resources.add(f":/{path}")
        require(sentinel in resources,
                f"Sentinel is not declared by {qrc_path}: {sentinel}")
        count += 1
    require(count > 0, "Static resource manifest is empty")
    return count


def verify_localization_report(app: Path, report_path: Path) -> None:
    require(report_path.is_file(), f"Missing device localization report: {report_path}")
    try:
        report = json.loads(report_path.read_text())
    except (ValueError, OSError) as error:
        fail(f"Invalid device localization report: {error}")
    require(isinstance(report, dict), "Device localization report must be an object")
    samples = report.get("samples", {})
    require(isinstance(samples, dict), "Missing runtime language samples")
    messages = {"performance": "Performance", "memoryLimit": "Memory Limit:", "fileMenu": "&File"}
    expected_samples = {"en_US": messages}
    for language in ("zh_CN", "zh_TW"):
        with (app / f"share/locale/{language}/LC_MESSAGES/krita.mo").open("rb") as stream:
            catalog = gettext.GNUTranslations(stream)
        expected_samples[language] = {key: catalog.gettext(text) for key, text in messages.items()}
        require(all(expected_samples[language][key] != text for key, text in messages.items()),
                f"Catalog has untranslated test strings: {language}")
    for language, expected in expected_samples.items():
        sample = samples.get(language, {})
        require(isinstance(sample, dict), f"Missing runtime sample: {language}")
        for key, value in expected.items():
            require(sample.get(key) == value,
                    f"Runtime localization mismatch: {language}/{key}: {sample.get(key)!r}, expected {value!r}")
    selected = str(report.get("languages", "")).split(":")[0]
    if selected in expected_samples:
        for key, value in expected_samples[selected].items():
            require(report.get(key) == value, f"Selected UI language mismatch: {selected}/{key}")
    print("Device localization report: zh_CN / zh_TW / English menu and settings translations PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    parser.add_argument("--build-dir", type=Path, default=PROJECT_ROOT / ".build/krita-ios")
    parser.add_argument("--signing", choices=("unsigned", "signed", "any"), default="unsigned")
    parser.add_argument("--localization-report", type=Path,
                        help="Opt-in ios-localization.json copied from this build on the device")
    args = parser.parse_args()

    app = args.app.resolve()
    require(app.is_dir(), f"Missing application bundle: {app}")
    info_path = app / "Info.plist"
    require(info_path.is_file(), "Missing Info.plist")
    try:
        plist = plistlib.loads(info_path.read_bytes())
    except (plistlib.InvalidFileException, ValueError) as error:
        fail(f"Invalid Info.plist: {error}")

    require(plist.get("UIDeviceFamily") == [2], "Expected an iPad-only application")
    executable_name = plist.get("CFBundleExecutable")
    require(isinstance(executable_name, str) and executable_name, "Missing CFBundleExecutable")
    executable = app / executable_name
    require(executable.is_file(), f"Missing executable: {executable}")

    arch = command("xcrun", "lipo", "-archs", str(executable)).stdout.strip()
    require(arch == "arm64", f"Unexpected architecture: {arch}")
    load_commands = command("xcrun", "otool", "-l", str(executable)).stdout
    platforms = set(re.findall(r"^\s*platform\s+(\S+)", load_commands, re.MULTILINE))
    require(platforms == {"2"}, f"Expected iOS device platform 2, found {platforms}")

    linked = command("xcrun", "otool", "-L", str(executable)).stdout
    for line in linked.splitlines()[1:]:
        dependency = line.strip().split(" (compatibility")[0]
        require(dependency.startswith(("/usr/lib/", "/System/Library/Frameworks/")),
                f"Unbundled dynamic dependency: {dependency}")

    for relative in (
        "etc/fonts/fonts.conf",
        "share/krita/actions/krita.action",
        "share/krita/paintoppresets",
        "share/locale/zh_CN/LC_MESSAGES/krita.mo",
        "share/locale/zh_TW/LC_MESSAGES/krita.mo",
        "share/locale/zh_CN/LC_MESSAGES/kconfig6_qt.qm",
        "share/locale/zh_TW/LC_MESSAGES/kconfig6_qt.qm",
    ):
        require((app / relative).exists(), f"Missing installed resource: {relative}")

    bundles = sorted((app / "share/krita").rglob("*.bundle"))
    require(bool(bundles), "No default resource bundles")
    for bundle in bundles:
        try:
            with zipfile.ZipFile(bundle) as archive:
                bad_file = archive.testzip()
        except zipfile.BadZipFile as error:
            fail(f"Invalid resource bundle {bundle.name}: {error}")
        require(bad_file is None, f"Corrupt resource bundle member: {bundle.name}:{bad_file}")

    require(not list(app.rglob("*.a")), "Static build archives must not be shipped")
    require(not [path for path in app.rglob("*") if path.is_symlink()],
            "Bundle contains unresolved symlinks")

    signing = command("codesign", "-dv", str(app), allow_failure=True)
    signing_text = f"{signing.stdout}\n{signing.stderr}"
    is_unsigned = signing.returncode != 0 and "not signed at all" in signing_text
    if args.signing == "unsigned":
        require(is_unsigned, "Expected an unsigned application bundle")
    elif args.signing == "signed":
        require(signing.returncode == 0, "Expected a signed application bundle")

    build_type, _ = load_build_type(args.build_dir.resolve())
    qrc_count = verify_qrc(executable, args.build_dir.resolve())
    if args.localization_report:
        verify_localization_report(app, args.localization_report.resolve())
    print(f"PASS: {app}")
    print(f"Build type: {build_type}; arm64 / iOS device; signing: {args.signing}")
    print(f"System dynamic dependencies only; default bundles: {len(bundles)}")
    print(f"Required static qrc resources: {qrc_count}; device launch: NOT VERIFIED")


if __name__ == "__main__":
    main()
