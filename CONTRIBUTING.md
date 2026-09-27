# Contributing

This repository is a build overlay for the pinned KDE Krita revision. Keep the
upstream source checkout, Qt kits, installed dependencies and build results in
the ignored directories documented in [the build guide](docs/ios/build.md).

1. Fetch the baseline with `packaging/ios/fetch-source.sh`, then apply the port
   with `packaging/ios/apply-krita-patch.sh`.
2. Make Krita changes in `upstream/krita/`. Keep platform adaptations guarded
   for iOS and retain existing copyright and license notices.
3. Export the port with `python3 packaging/ios/export-krita-patch.py`. This
   includes added source files and checks reverse application; it does not
   stage or commit anything.
4. Put dependency changes in `patches/ios/dependencies/<package>/*.patch`, or
   the existing `<package>-no-process.patch` convention. Keep the dependency
   revision recorded in the build script.
5. Run `python3 packaging/ios/check-repository.py --check-patches` with the
   pinned checkouts available. Run the relevant host regressions or iPad
   checks when behavior changes. Record build-only and device-tested results
   separately.
6. Describe the concrete behavior changed and the validation performed.

`logs/`, signing identities, device reports, provisioning profiles, generated
Xcode projects and application bundles stay local. The submission checker reads
the Git candidate set, so it also rejects ignored files that were force-added.

CI runs repository, syntax and documentation checks without Qt, Apple accounts
or device access. A passing CI job is not an iPadOS build or runtime test.

For a bug report, include the build revision, iPadOS version, reproduction steps
and relevant diagnostics. Remove personal paths, device identifiers and signing
details before sharing reports.
