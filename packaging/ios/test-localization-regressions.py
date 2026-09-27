#!/usr/bin/env python3
"""Test catalog initialization with real host KI18n and the shipped .mo files.

Builds only the pinned KI18n host library, not the Krita desktop application.
Extracts the production registration helper so the test exercises its paths.
The separate opt-in iOS diagnostic validates the target libintl on the device.
"""
import gettext
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
HOST_QT = ROOT / ".qt/6.10.3/macos"
KI18N_SOURCE = ROOT / ".deps/src/ki18n"
KI18N_BUILD = ROOT / ".build/locale-tests/ki18n-host"
APP = ROOT / ".build/krita-ios-xcode/bin/Release/krita.app"


def run(*args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def main():
    source = (ROOT / "upstream/krita/krita/main.cc").read_text()
    start = source.index("void registerIosTranslationCatalogs(")
    end = source.index("\n}\n", start) + 3
    helper = source[start:end]
    # The regression is about startup order as well as the helper's contents.
    assert source.index("registerIosTranslationCatalogs(root);") < source.index("KisApplication app(key, argc, argv);")
    assert source.index("registerIosTranslationCatalogs(root);") < source.index("installTranslators(app);")
    target_symbols = run("xcrun", "nm", "-u", ROOT / ".deps/ios/lib/libKF6I18n.a",
                         capture_output=True, text=True).stdout
    assert "__nl_msg_cat_cntr" in target_symbols, "iOS KI18n must invalidate gettext's language cache"

    run("cmake", "-S", KI18N_SOURCE, "-B", KI18N_BUILD, "-G", "Ninja",
        f"-DECM_DIR={ROOT / '.deps/host/share/ECM/cmake'}",
        f"-DCMAKE_PREFIX_PATH={HOST_QT};{ROOT / '.deps/host'}",
        "-DBUILD_TESTING=OFF", "-DBUILD_WITH_QML=OFF", "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_BUILD_TYPE=Release", "-DLibIntl_INCLUDE_DIRS=/opt/homebrew/include",
        "-DLibIntl_LIBRARIES=/opt/homebrew/lib/libintl.dylib")
    run("cmake", "--build", KI18N_BUILD, "--target", "KF6I18n", "--parallel", "4")

    fixture = r'''
#include <KLocalizedString>
#include <QCoreApplication>
#include <QDir>
#include <QJsonDocument>
#include <QJsonObject>
#include <cstdio>
#include <locale.h>
''' + helper + r'''
int main(int argc, char **argv) {
    const QString root = QString::fromLocal8Bit(argv[1]) + QLatin1Char('/');
    const bool late = QString::fromLatin1(argv[2]) == QStringLiteral("late");
    QJsonObject report;
    {
        QCoreApplication temporary(argc, argv);
        report.insert(QStringLiteral("numericBeforeRegistration"), QString::fromLatin1(setlocale(LC_NUMERIC, nullptr)));
        if (!late) registerIosTranslationCatalogs(root);
        KLocalizedString::setLanguages({QStringLiteral("zh_CN")});
        report.insert(QStringLiteral("firstLookup"), i18nd("krita", "Performance"));
        if (late) registerIosTranslationCatalogs(root);
        report.insert(QStringLiteral("numericAfterRegistration"), QString::fromLatin1(setlocale(LC_NUMERIC, nullptr)));
    }
    QCoreApplication application(argc, argv);
    for (const QString &language : {QStringLiteral("zh_CN"), QStringLiteral("zh_TW"), QStringLiteral("en_US")}) {
        KLocalizedString::setLanguages({language});
        QJsonObject sample;
        sample.insert(QStringLiteral("performance"), i18n("Performance"));
        sample.insert(QStringLiteral("memoryLimit"), i18n("Memory Limit:"));
        sample.insert(QStringLiteral("fileMenu"), i18n("&File"));
        sample.insert(QStringLiteral("copyAction"), i18nc("action", "Copy"));
        report.insert(language, sample);
    }
    report.insert(QStringLiteral("numericLocale"), QString::fromLatin1(setlocale(LC_NUMERIC, nullptr)));
    const QByteArray output = QJsonDocument(report).toJson(QJsonDocument::Compact);
    std::puts(output.constData());
}
'''
    # gettext ignores LANGUAGE if LC_ALL is C, including the shell's C.UTF-8.
    # Match the device's gettext environment without overriding locale categories.
    environment = dict(os.environ)
    environment.pop("LC_ALL", None)
    environment.pop("LC_MESSAGES", None)
    environment.update(LANG="zh_CN.UTF-8", LANGUAGE="zh_CN")
    with tempfile.TemporaryDirectory(prefix="krita-localization-regression-") as directory:
        cpp = Path(directory) / "regression.cpp"
        binary = Path(directory) / "regression"
        cpp.write_text(fixture)
        run("xcrun", "clang++", "-std=c++17", "-fPIC", "-DKI18N_STATIC_DEFINE",
            f"-I{KI18N_BUILD / 'src/i18n'}", f"-I{KI18N_SOURCE / 'src/i18n'}",
            f"-I{HOST_QT / 'lib/QtCore.framework/Headers'}",
            f"-I{KI18N_BUILD}", f"-F{HOST_QT / 'lib'}", cpp,
            KI18N_BUILD / "lib/libKF6I18n.a", "-framework", "QtCore",
            "/opt/homebrew/lib/libintl.dylib", f"-Wl,-rpath,{HOST_QT / 'lib'}", "-o", binary)
        late = json.loads(run(binary, APP, "late", env=environment, capture_output=True, text=True).stdout)
        assert late["firstLookup"] == "Performance", late
        assert late["zh_CN"]["performance"] == "Performance", late
        early = json.loads(run(binary, APP, "early", env=environment, capture_output=True, text=True).stdout)
        assert early["numericAfterRegistration"] == early["numericBeforeRegistration"], early
        assert early["firstLookup"] == "性能", early
        messages = {"performance": "Performance", "memoryLimit": "Memory Limit:", "fileMenu": "&File"}
        for language in ("zh_CN", "zh_TW"):
            with (APP / f"share/locale/{language}/LC_MESSAGES/krita.mo").open("rb") as stream:
                catalog = gettext.GNUTranslations(stream)
            for key, text in messages.items():
                expected = catalog.gettext(text)
                assert expected != text, (language, text)
                assert early[language][key] == expected, (language, key, early)
            assert early[language]["copyAction"] == catalog.pgettext("action", "Copy"), early
        assert early["en_US"] == {**messages, "copyAction": "Copy"}, early
        print(json.dumps(early, ensure_ascii=False, indent=2))
    print("PASS: reproduces cached miss; early registration survives application recreation; zh_CN/zh_TW/menu/settings/context/English; registration leaves numeric locale unchanged")


if __name__ == "__main__":
    main()
