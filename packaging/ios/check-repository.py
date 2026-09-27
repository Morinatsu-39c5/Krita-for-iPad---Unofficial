#!/usr/bin/env python3
"""Read-only checks of Git submission candidates; optionally validate patch bases.

Runs with Python's standard library, Git and Bash on Linux or macOS. No build,
network access, credentials, staging or commits are required.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_ROOT_FILES = {
    ".gitignore", ".gitattributes", ".env.example", "README.md", "LICENSE",
    "NOTICE.md", "CONTRIBUTING.md",
}
ALLOWED_DIRS = {".github", "LICENSES", "docs", "packaging", "patches"}
MAX_FILE_BYTES = 2 * 1024 * 1024


def command(*args, cwd=ROOT, **kwargs):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, check=True,
                          capture_output=True, **kwargs)


def candidates():
    output = command("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z").stdout
    return sorted({os.fsdecode(name) for name in output.split(b"\0") if name})


def check_files(names):
    errors = []
    total = 0
    required = ALLOWED_ROOT_FILES | {".github/workflows/repository-check.yml", "patches/ios/baselines.json"}
    errors.extend(f"Missing submission file: {name}" for name in sorted(required - set(names)))
    private_patterns = [
        re.compile(r"/(?:Users|home)/[a-zA-Z0-9._-]+/"),
        re.compile(r"/Application/[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}/"),
        re.compile(r"(?:Team ID|TeamIdentifier|TEAM_ID|Team)\s*(?:[:=]|为)?\s*[`\"']?(?!X{10}\b)[A-Z0-9]{10}\b"),
        re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(r"-----BEGIN(?: RSA| EC| OPENSSH)? PRIVATE KEY-----"),
    ]
    for name in names:
        path = ROOT / name
        relative = Path(name)
        if (relative.parts[0] not in ALLOWED_DIRS and name not in ALLOWED_ROOT_FILES):
            errors.append(f"Unexpected submission path: {name}")
        if path.is_symlink() or not path.is_file():
            errors.append(f"Submission must contain ordinary files: {name}")
            continue
        if ("__pycache__" in relative.parts or "xcuserdata" in relative.parts or
            any(part.endswith((".app", ".dSYM", ".xcarchive", ".xcodeproj", ".xcworkspace")) for part in relative.parts) or
            path.suffix in {".pyc", ".ipa", ".ips", ".p12", ".pfx", ".pem", ".key",
                            ".cer", ".crt", ".mobileprovision", ".provisionprofile"}):
            errors.append(f"Local output or signing material in submission: {name}")
        data = path.read_bytes()
        total += len(data)
        if len(data) > MAX_FILE_BYTES:
            errors.append(f"File exceeds source-only size limit: {name}")
        if path.suffix == ".png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                errors.append(f"Invalid PNG asset: {name}")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"Unexpected binary file: {name}")
            continue
        if "\r" in text or "\0" in text:
            errors.append(f"Non-LF or binary text: {name}")
        for pattern in private_patterns:
            if pattern.search(text):
                # Avoid printing the matching identity or token in CI output.
                errors.append(f"Local identity, path or credential pattern: {name}")
                break
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=name)
            except SyntaxError as error:
                errors.append(f"Python syntax: {name}:{error.lineno}")
        if path.suffix == ".sh":
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                errors.append(f"Bash syntax: {name}: {result.stderr.strip()}")
            if not os.access(path, os.X_OK):
                errors.append(f"Shell entry point is not executable: {name}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except ValueError:
                errors.append(f"Invalid JSON: {name}")
        if path.suffix in {".patch", ".reference"}:
            try:
                command("git", "apply", "--numstat", str(path))
            except subprocess.CalledProcessError:
                errors.append(f"Malformed patch: {name}")
        if path.suffix == ".md":
            # Check links outside code blocks against the submitted file set.
            prose = re.sub(r"(?ms)^```[^\n]*\n.*?^```[^\n]*$", "", text)
            for link in re.findall(r"\]\((<[^>]+>|[^)]+)\)", prose):
                target = link.strip("<>").split(' "', 1)[0]
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                absolute = (path.parent / unquote(parsed.path)).resolve()
                try:
                    destination = absolute.relative_to(ROOT).as_posix()
                except ValueError:
                    errors.append(f"Link escapes repository: {name}")
                    continue
                if destination not in names and not any(item.startswith(destination + "/") for item in names):
                    errors.append(f"Link is absent from submission: {name} -> {destination}")
    if errors:
        raise SystemExit("FAIL:\n" + "\n".join(errors))
    print(f"PASS: {len(names)} source/documentation files; {total:,} bytes; syntax, links, patch format and local-data checks")


def check_patch_group(package, checkout, revision, patches):
    actual = command("git", "rev-parse", "HEAD", cwd=checkout, text=True).stdout.strip()
    if actual != revision:
        raise SystemExit(f"FAIL: unexpected baseline for {package}: {actual}")
    paths = set()
    for patch in patches:
        for old, new in re.findall(r"(?m)^diff --git a/(.+) b/(.+)$", patch.read_text()):
            paths.update((old, new))
    with tempfile.TemporaryDirectory(prefix="krita-patch-baseline-") as directory:
        clean = Path(directory)
        before = {}
        for name in sorted(paths):
            # Added files have no entry in the base; don't copy them from the
            # locally patched checkout. Recover baseline bytes straight from Git.
            entry = subprocess.run(["git", "ls-tree", revision, "--", name], cwd=checkout,
                                   capture_output=True, text=True, check=True).stdout
            if not entry:
                continue
            mode = entry.split()[0]
            if mode not in {"100644", "100755"}:
                raise SystemExit(f"FAIL: unsupported patch baseline mode: {package}/{name}")
            data = command("git", "show", f"{revision}:{name}", cwd=checkout).stdout
            target = clean / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if mode == "100755" else 0o644)
            before[name] = (data, target.stat().st_mode & 0o777)
        for patch in patches:
            command("git", "apply", "--check", str(patch), cwd=clean)
            command("git", "apply", str(patch), cwd=clean)
        for patch in reversed(patches):
            command("git", "apply", "--reverse", "--check", str(patch), cwd=clean)
            command("git", "apply", "--reverse", str(patch), cwd=clean)
        after = {path.relative_to(clean).as_posix(): (path.read_bytes(), path.stat().st_mode & 0o777)
                 for path in clean.rglob("*") if path.is_file()}
        if after != before:
            raise SystemExit(f"FAIL: patch reversal did not restore clean baseline: {package}")
    print(f"PASS: {package}; {len(patches)} patches apply and reverse on {revision}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-patches", action="store_true", help="Require local pinned checkouts; no downloads")
    parser.add_argument("--manifest", type=Path, help="Write a SHA256/size list of submission candidates")
    args = parser.parse_args()
    names = candidates()
    check_files(names)
    if args.check_patches:
        bases = json.loads((ROOT / "patches/ios/baselines.json").read_text())
        check_patch_group("krita", ROOT / "upstream/krita", bases["krita"]["revision"],
                          [ROOT / "patches/ios/krita-ipados.patch"])
        for package, baseline in bases["patchedDependencies"].items():
            patches = sorted((ROOT / "patches/ios/dependencies" / package).glob("*.patch"))
            legacy = ROOT / f"patches/ios/{package}-no-process.patch"
            if legacy.exists():
                patches.insert(0, legacy)
            if not patches:
                raise SystemExit(f"FAIL: no patches for recorded dependency: {package}")
            check_patch_group(package, ROOT / ".deps/src" / package, baseline["revision"], patches)
    else:
        print("Patch baseline checks not requested; use --check-patches with the pinned local sources")
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"path": name, "bytes": (ROOT / name).stat().st_size,
                 "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()} for name in names]
        args.manifest.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
        print(f"Submission manifest: {args.manifest}")


if __name__ == "__main__":
    main()
