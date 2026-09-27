#!/usr/bin/env python3
"""Exercise the production iOS popup callbacks with Qt Widgets on macOS.

The native input responder and document saving are deterministic test doubles;
timers, focus, event filters and message boxes use the installed host Qt kit.
This does not validate UIKit's picker or touch delivery on a physical iPad.
"""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
manager = (root / "upstream/krita/libs/ui/input/kis_input_manager.cpp").read_text()
view = (root / "upstream/krita/libs/ui/KisView.cpp").read_text()
guard = manager[manager.index('constexpr auto s_iosExplicitTextInputProperty'):manager.index('void updateIosInputMethod(')]
close = view[view.index('bool KisView::queryClose()'):view.index('void KisView::slotMigratedToScreen(')]
host_lib = root / ".qt/6.10.3/macos/lib"

preamble = r'''
#include <QtWidgets/QApplication>
#include <QtWidgets/QAbstractSpinBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QPlainTextEdit>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QMessageBox>
#include <QtCore/QTimer>
#include <QtCore/QPointer>
#include <QtCore/QFileInfo>
#include <QtCore/QElapsedTimer>
#include <QtCore/QThread>
#include <QtGui/QInputMethod>
#include <QtGui/QInputMethodEvent>
#include <QtGui/QMouseEvent>
#include <memory>
#include <iostream>
#include <stdexcept>
void check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
void pump(int ms = 10) {
    QElapsedTimer timer; timer.start();
    do { QApplication::processEvents(); QThread::msleep(1); } while (timer.elapsed() < ms);
}
struct FakeInputMethod {
    bool visible = true; int resets = 0, hides = 0;
    bool isVisible() const { return visible; }
    void reset() { ++resets; }
    void hide() { ++hides; visible = false; }
} inputMethod;
struct FakeGuiApplication {
    static QObject *focusObject() { return QApplication::focusWidget(); }
    static FakeInputMethod *inputMethod() { return &::inputMethod; }
};
#define QGuiApplication FakeGuiApplication
#define QInputMethod FakeInputMethod
'''

document = r'''
#undef QGuiApplication
#undef QInputMethod
#define Q_OS_IOS
QString i18n(const char *text, const QString &value) { return QString::fromUtf8(text).arg(value); }
QString i18n(const char *text) { return QString::fromUtf8(text); }
QString i18nc(const char *, const char *text) { return QString::fromUtf8(text); }
struct FakeImage {
    int cancellations = 0, ends = 0; bool idle = true;
    void requestStrokeCancellation() { ++cancellations; }
    void requestStrokeEnd() { ++ends; }
    bool isIdle(bool = false) const { return idle; }
};
using KisImageSP = std::shared_ptr<FakeImage>;
struct KisDocument : QObject {
    bool saving = false, modified = true, removedAutosave = false;
    KisImageSP img = std::make_shared<FakeImage>();
    bool isSaving() const { return saving; }
    bool isModified() const { return modified; }
    void setModified(bool value) { modified = value; }
    QString path() const { return {}; }
    QString localFilePath() const { return {}; }
    bool isRecovered() const { return false; }
    void removeAutoSaveFiles(const QString &, bool) { removedAutosave = true; }
    QByteArray mimeType() const { return "application/x-krita"; }
    QByteArray nativeFormatMimeType() const { return mimeType(); }
    KisImageSP image() const { return img; }
};
struct FakeWindow : QWidget {
    enum SaveResult { Success, StartFailure, BackgroundFailure, ModifiedDuringSave };
    SaveResult result = Success;
    bool saveDocument(KisDocument *doc, bool, bool) {
        if (result == StartFailure) return false;
        doc->saving = true;
        const bool success = result == Success;
        QTimer::singleShot(20, doc, [doc, success] { doc->saving = false; doc->modified = !success; });
        return true;
    }
    void blockUntilOperationsFinishedForced(KisImageSP) {}
};
struct KisView : QWidget {
    struct Private { bool iosClosePending = false; QPointer<QMessageBox> iosClosePrompt; } storage, *d = &storage;
    KisDocument doc;
    FakeWindow window;
    int closed = 0;
    ~KisView() override {
        if (d->iosClosePrompt) { d->iosClosePrompt->disconnect(this); delete d->iosClosePrompt; }
    }
    KisDocument *document() { return &doc; }
    FakeWindow *mainWindow() { return &window; }
    FakeWindow *viewManager() { return &window; }
    void closeView() { if (queryClose()) ++closed; }
    bool queryClose();
    void requestIosCloseConfirmation();
    void waitForIosSaveBeforeClose(bool closeAfterSave);
};
'''

tests = r'''
class PickerFilter : public QObject {
public:
    bool eventFilter(QObject *, QEvent *event) override {
        if (event->type() != QEvent::InputMethodQuery) return false;
        auto *query = static_cast<QInputMethodQueryEvent *>(event);
        query->setValue(Qt::ImPlatformData, QVariantMap{{"inputView", QVariant::fromValue(static_cast<void *>(this))}});
        return true;
    }
};
void answer(KisView &view, int result) {
    check(!view.queryClose(), "modified close must return immediately without accepting");
    check(!view.d->iosClosePrompt, "prompt must be deferred until the close event returns");
    check(!view.queryClose(), "repeated close must not open a second prompt");
    pump();
    auto *prompt = view.d->iosClosePrompt.data();
    check(prompt != nullptr, "one prompt must be visible");
    check(prompt->testOption(QMessageBox::Option::DontUseNativeDialog), "confirmation must bypass native alert");
    prompt->done(result);
    check(view.closed == 0, "document must not close in dialog completion callback");
    pump(260);
}
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    try {
        QWidget host; QLineEdit editor(&host); QWidget canvas(&host);
        host.show(); host.activateWindow(); canvas.setFocusPolicy(Qt::StrongFocus); canvas.setFocus(); pump();
        check(QApplication::focusWidget() == &canvas, "test requires real widget focus");
        PickerFilter picker; canvas.installEventFilter(&picker);
        hideIosInputMethod();
        check(inputMethod.resets == 0 && inputMethod.hides == 0, "native picker must survive keyboard protection");
        canvas.removeEventFilter(&picker);
        hideIosInputMethod();
        check(inputMethod.resets == 1 && inputMethod.hides == 1, "ordinary non-text keyboard must hide");
        hideIosInputMethod();
        check(inputMethod.resets == 1, "hidden input panel must not recreate responder");
        IosInputMethodGuard guard(&app); app.installEventFilter(&guard);
        inputMethod.visible = true;
        QMouseEvent click(QEvent::MouseButtonPress, QPointF(2, 2), QPointF(2, 2),
                          Qt::LeftButton, Qt::LeftButton, Qt::NoModifier);
        QCoreApplication::sendEvent(&canvas, &click);
        editor.setFocus(); pump();
        check(inputMethod.hides == 1, "queued non-text hide must respect new text-editor focus");
        canvas.setFocus();
        for (int i = 0; i < 4; ++i) QCoreApplication::sendEvent(&canvas, &click);
        pump();
        check(inputMethod.hides == 2, "queued non-text hides must coalesce");
        app.removeEventFilter(&guard); host.hide(); pump();
        { KisView view; answer(view, QMessageBox::Cancel); check(view.closed == 0 && view.doc.modified, "cancel must retain edits"); }
        { KisView view; answer(view, QMessageBox::No); check(view.closed == 1 && view.doc.removedAutosave, "discard must close once and remove autosave"); }
        { KisView view; answer(view, QMessageBox::Yes); check(view.closed == 1 && !view.doc.saving && !view.doc.modified, "save must finish before closing"); }
        for (auto failure : {FakeWindow::StartFailure, FakeWindow::BackgroundFailure, FakeWindow::ModifiedDuringSave}) {
            KisView view; view.window.result = failure; answer(view, QMessageBox::Yes);
            check(view.closed == 0 && view.doc.modified, "failed or out-of-date save must preserve document");
        }
        { KisView view; view.doc.img->idle = false; answer(view, QMessageBox::No);
          check(view.closed == 0 && view.doc.modified && view.doc.img->cancellations == 1, "busy discard must wait without clearing edits");
          view.doc.img->idle = true; pump(140); check(view.closed == 1, "idle discard must finish asynchronously"); }
        { KisView view; view.doc.img->idle = false; answer(view, QMessageBox::Yes);
          check(view.closed == 0 && !view.doc.saving && view.doc.img->ends == 1, "busy image must finish its stroke before saving");
          view.doc.img->idle = true; pump(260); check(view.closed == 1, "save must close only after image and saving finish"); }
        { KisView view; view.doc.saving = true;
          check(!view.queryClose(), "save in progress must defer close");
          view.doc.saving = false; pump(140);
          check(view.closed == 0 && view.d->iosClosePrompt, "failed existing save must return to confirmation");
          view.d->iosClosePrompt->done(QMessageBox::Cancel); pump(); }
        { auto *view = new KisView; view->queryClose(); delete view; pump();
          check(!QApplication::activeModalWidget(), "destroyed view must cancel deferred prompt"); }
        { auto *view = new KisView; view->queryClose(); pump(); delete view; pump();
          check(!QApplication::activeModalWidget(), "destroyed view must dismiss live prompt"); }
        std::cout << "PASS: picker preservation, real editor focus, coalesced keyboard hide, asynchronous cancel/discard/save, busy image, save failures, edits during saving, existing save and view destruction\n";
    } catch (const std::exception &error) { std::cerr << "FAIL: " << error.what() << '\n'; return 1; }
}
'''

with tempfile.TemporaryDirectory(prefix="krita-popup-regression-") as temp:
    cpp = Path(temp) / "regression.cpp"
    binary = Path(temp) / "regression"
    cpp.write_text(preamble + guard + document + close + tests)
    subprocess.run([
        "xcrun", "clang++", "-std=c++17", "-fPIC", f"-F{host_lib}",
        str(cpp), "-framework", "QtWidgets", "-framework", "QtGui", "-framework", "QtCore",
        f"-Wl,-rpath,{host_lib}", "-o", str(binary)
    ], check=True)
    subprocess.run([str(binary)], check=True, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
