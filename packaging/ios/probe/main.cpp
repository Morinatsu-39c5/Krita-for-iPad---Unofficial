// SPDX-License-Identifier: GPL-3.0-or-later
// Standalone platform probe; not a replacement for Krita's canvas or UI scaling.
#include <QtWidgets>
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
#include <QTabletEvent>
#include <QTouchEvent>
#include <QSaveFile>
#include <functional>
#ifdef Q_OS_IOS
#include "FilesExport.h"
#endif

class ProbeStyle final : public QProxyStyle
{
public:
    ProbeStyle() : QProxyStyle(QStyleFactory::create("Fusion")) {}
    qreal factor = 1.5;
    int pixelMetric(PixelMetric metric, const QStyleOption *option = nullptr,
                    const QWidget *widget = nullptr) const override
    {
        const int base = QProxyStyle::pixelMetric(metric, option, widget);
        switch (metric) {
        case PM_SmallIconSize: case PM_LargeIconSize: case PM_ToolBarIconSize:
        case PM_ButtonMargin: case PM_ScrollBarExtent: case PM_ScrollBarSliderMin:
        case PM_SliderThickness: case PM_SliderLength: case PM_DockWidgetTitleMargin:
        case PM_ToolBarItemMargin: case PM_MenuPanelWidth: case PM_MenuHMargin:
        case PM_MenuVMargin: case PM_TabBarTabHSpace: case PM_TabBarTabVSpace:
        case PM_IndicatorWidth: case PM_IndicatorHeight:
            return qRound(base * factor);
        default: return base;
        }
    }
};

class Canvas final : public QWidget
{
public:
    Canvas() : pixels(1024, 768, QImage::Format_ARGB32_Premultiplied)
    {
        pixels.fill(Qt::white);
        setAttribute(Qt::WA_AcceptTouchEvents);
        setFocusPolicy(Qt::StrongFocus);
        setMinimumSize(160, 120);
    }
    QImage pixels;
    QPointF pan;
    std::function<void(const QString &)> report;
    int tabletCount = 0;
    int strokeCount = 0;
    void clear() { pixels.fill(Qt::white); update(); }
    QPointF imagePoint(QPointF p) const { return p - pan; }
protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        p.fillRect(rect(), QColor("#dddddd"));
        // Image has DPR 1: one document pixel per logical widget coordinate.
        // Qt alone maps logical widget coordinates to the display's native DPR.
        p.drawImage(pan, pixels);
        p.setPen(QColor("#b0b0b0"));
        for (int x = 0; x < pixels.width(); x += 100)
            p.drawLine(QPointF(x, 0) + pan, QPointF(x, pixels.height()) + pan);
        for (int y = 0; y < pixels.height(); y += 100)
            p.drawLine(QPointF(0, y) + pan, QPointF(pixels.width(), y) + pan);
    }
    void tabletEvent(QTabletEvent *e) override
    {
        ++tabletCount;
        const auto point = imagePoint(e->position());
        if (e->type() == QEvent::TabletPress) {
            penDown = true;
            previous = point;
        }
        if (penDown && e->type() != QEvent::TabletRelease)
            stroke(previous, point, e->pressure());
        previous = point;
        if (e->type() == QEvent::TabletRelease) penDown = false;
        if (report) report(QString("tablet #%1 type=%2 pos=(%3,%4) image=(%5,%6) pressure=%7 tilt=(%8,%9) DPR=%10")
            .arg(tabletCount).arg(int(e->type())).arg(e->position().x()).arg(e->position().y())
            .arg(point.x()).arg(point.y()).arg(e->pressure()).arg(e->xTilt()).arg(e->yTilt()).arg(devicePixelRatioF()));
        e->accept();
    }
    bool event(QEvent *e) override
    {
        if (e->type() == QEvent::TouchBegin || e->type() == QEvent::TouchUpdate ||
            e->type() == QEvent::TouchEnd || e->type() == QEvent::TouchCancel) {
            const auto *touch = static_cast<QTouchEvent *>(e);
            QPointF center;
            for (const auto &point : touch->points()) center += point.position();
            const int count = int(touch->points().size());
            if (count) center /= count;
            if (e->type() == QEvent::TouchUpdate && count == touchCount && !penDown)
                pan += center - lastTouch;
            lastTouch = center;
            touchCount = count;
            if (e->type() == QEvent::TouchEnd || e->type() == QEvent::TouchCancel) touchCount = 0;
            if (report) report(QString("touch type=%1 fingers=%2; pan only, no paint").arg(int(e->type())).arg(count));
            update();
            e->accept();
            return true;
        }
        return QWidget::event(e);
    }
    void mousePressEvent(QMouseEvent *e) override
    {
        if (e->source() != Qt::MouseEventNotSynthesized || e->button() != Qt::LeftButton) return;
        mouseDown = true;
        previous = imagePoint(e->position());
        stroke(previous, previous, 0.5);
    }
    void mouseMoveEvent(QMouseEvent *e) override
    {
        if (!mouseDown || e->source() != Qt::MouseEventNotSynthesized) return;
        const auto point = imagePoint(e->position());
        stroke(previous, point, 0.5);
        previous = point;
    }
    void mouseReleaseEvent(QMouseEvent *) override { mouseDown = false; }
private:
    void stroke(QPointF from, QPointF to, qreal pressure)
    {
        QPainter p(&pixels);
        p.setRenderHint(QPainter::Antialiasing);
        p.setPen(QPen(Qt::black, qMax(0.5, pressure * 16), Qt::SolidLine, Qt::RoundCap));
        if (from == to) p.drawPoint(to); else p.drawLine(from, to);
        ++strokeCount;
        update();
    }
    QPointF previous, lastTouch;
    bool penDown = false, mouseDown = false;
    int touchCount = 0;
};

class GLProbe final : public QOpenGLWidget, protected QOpenGLFunctions
{
public:
    std::function<void(const QString &)> report;
protected:
    void initializeGL() override
    {
        initializeOpenGLFunctions();
        if (report) report(QString("OpenGL initialized: %1 / %2")
            .arg(QString::fromLatin1(reinterpret_cast<const char *>(glGetString(GL_VERSION))))
            .arg(QString::fromLatin1(reinterpret_cast<const char *>(glGetString(GL_RENDERER)))));
    }
    void paintGL() override
    {
        glClearColor(0.1f, 0.3f, 0.35f, 1.f);
        glClear(GL_COLOR_BUFFER_BIT);
        QPainter p(this);
        p.setPen(Qt::white);
        p.drawText(rect(), Qt::AlignCenter, QString("QOpenGLWidget frame %1").arg(++frames));
    }
private:
    int frames = 0;
};

int main(int argc, char **argv)
{
    QApplication::setAttribute(Qt::AA_SynthesizeMouseForUnhandledTouchEvents, false);
    QApplication::setAttribute(Qt::AA_SynthesizeMouseForUnhandledTabletEvents, false);
    QApplication app(argc, argv);
    app.setOrganizationName("KritaIOSProbe");
    app.setApplicationName("KritaIOSProbe");
    auto *style = new ProbeStyle;
    app.setStyle(style);
    const QFont baseFont = app.font();
    auto applyScale = [&](int percent) {
        style->factor = percent / 100.0;
        QFont font = baseFont;
        if (baseFont.pointSizeF() > 0) font.setPointSizeF(baseFont.pointSizeF() * style->factor);
        else font.setPixelSize(qRound(baseFont.pixelSize() * style->factor));
        app.setFont(font);
        for (QWidget *w : app.allWidgets()) {
            QEvent change(QEvent::StyleChange);
            QApplication::sendEvent(w, &change);
            w->updateGeometry();
            w->update();
        }
    };
    if (app.arguments().contains("--self-test")) {
        Canvas c;
        const QPointF point(123.25, 234.5);
        for (int scale : {100, 125, 150, 175, 200}) {
            applyScale(scale);
            if (c.pixels.size() != QSize(1024, 768) || c.pixels.devicePixelRatio() != 1 || c.imagePoint(point) != point)
                return 1;
        }
        c.pan = QPointF(20, 30);
        if (c.imagePoint(point) != QPointF(103.25, 204.5)) return 2;
        QPointingDevice pen("test pen", 1, QInputDevice::DeviceType::Stylus,
            QPointingDevice::PointerType::Pen, QInputDevice::Capability::Position | QInputDevice::Capability::Pressure, 1, 1);
        for (auto type : {QEvent::TabletPress, QEvent::TabletMove, QEvent::TabletRelease}) {
            QTabletEvent event(type, &pen, point, point, 0.7, 15, 25, 0, 0, 0,
                Qt::NoModifier, Qt::LeftButton, type == QEvent::TabletRelease ? Qt::NoButton : Qt::LeftButton);
            QApplication::sendEvent(&c, &event);
        }
        if (c.tabletCount != 3 || c.strokeCount != 2 || c.pixels.pixelColor(103, 205) == QColor(Qt::white)) return 3;
        const QImage before = c.pixels;
        QMouseEvent synthetic(QEvent::MouseButtonPress, point, point, point, Qt::LeftButton,
            Qt::LeftButton, Qt::NoModifier, Qt::MouseEventSynthesizedByQt);
        QApplication::sendEvent(&c, &synthetic);
        if (before != c.pixels) return 4;
        qInfo("PASS: five UI scales, fixed image pixels, pan mapping, synthetic tablet pressure path, synthesized mouse rejection");
        return 0;
    }

    QMainWindow window;
    window.setWindowTitle("Krita iPadOS — Qt Widgets platform probe");
    auto *canvas = new Canvas;
    auto *tabs = new QTabWidget;
    tabs->addTab(canvas, "Pencil / raster");
    window.setCentralWidget(tabs);
    auto *logView = new QPlainTextEdit;
    logView->setReadOnly(true);
    logView->setMaximumBlockCount(500);
    auto *dock = new QDockWidget("Input and platform evidence", &window);
    dock->setWidget(logView);
    window.addDockWidget(Qt::BottomDockWidgetArea, dock);
    const QString documents = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation);
    const QString data = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(documents);
    QDir().mkpath(data);
    QDir().mkpath(QStandardPaths::writableLocation(QStandardPaths::CacheLocation));
    QFile evidence(documents + "/probe-events.txt");
    if (!evidence.open(QIODevice::WriteOnly | QIODevice::Truncate | QIODevice::Text))
        qWarning() << "Cannot save event evidence:" << evidence.errorString();
    auto report = [&](const QString &message) {
        logView->appendPlainText(message);
        evidence.write((message + '\n').toUtf8());
        evidence.flush();
        qInfo().noquote() << message;
    };
    canvas->report = report;
    auto *toolbar = window.addToolBar("Probe controls");
    toolbar->setMovable(false);
    auto *fileMenu = window.menuBar()->addMenu("File");
    window.menuBar()->setNativeMenuBar(false);
    auto addAction = [&](const QString &text, const QKeySequence &shortcut, auto callback) {
        auto *action = fileMenu->addAction(text);
        action->setShortcut(shortcut);
        toolbar->addAction(action);
        QObject::connect(action, &QAction::triggered, &window, callback);
    };
    addAction("Open / import", QKeySequence::Open, [&] {
        auto *dialog = new QFileDialog(&window, "Open document or resource", documents);
        dialog->setAttribute(Qt::WA_DeleteOnClose);
        dialog->setFileMode(QFileDialog::ExistingFile);
        // Request native dialog without forcing a PicturesLocation photo picker.
        QObject::connect(dialog, &QFileDialog::fileSelected, &window, [&](const QString &path) {
            QFile input(path);
            if (!input.open(QIODevice::ReadOnly)) { report("Import failed: " + input.errorString()); return; }
            const QString imports = data + "/imports";
            QDir().mkpath(imports);
            const QString dest = imports + "/" + QUuid::createUuid().toString(QUuid::WithoutBraces) + "-" + QFileInfo(path).fileName();
            QSaveFile output(dest);
            if (!output.open(QIODevice::WriteOnly)) { report(output.errorString()); return; }
            while (!input.atEnd()) {
                const QByteArray block = input.read(1024 * 1024);
                if (input.error() != QFileDevice::NoError || output.write(block) != block.size()) {
                    report("Import copy failed"); output.cancelWriting(); return;
                }
            }
            if (!output.commit()) { report(output.errorString()); return; }
            report("Copied selected data to sandbox: " + dest);
            // Resource data is only copied in this probe; Krita indexing is phase 4.
        });
        dialog->open();
    });
    addAction("Export PNG", QKeySequence::SaveAs, [&] {
#ifdef Q_OS_IOS
        auto staging = std::make_shared<QTemporaryDir>(QStandardPaths::writableLocation(QStandardPaths::CacheLocation) + "/export-XXXXXX");
        // The directory must exist before QTemporaryDir creates its child.
        if (!staging->isValid()) { report("Cannot create export staging directory"); return; }
        const QString path = staging->path() + "/probe.png";
        if (!canvas->pixels.save(path, "PNG")) { report("Cannot stage PNG"); return; }
        exportToFiles(&window, path, [&, staging](bool, const QString &message) { report(message); });
#else
        auto *dialog = new QFileDialog(&window, "Export probe PNG", documents + "/probe.png", "PNG (*.png)");
        dialog->setAttribute(Qt::WA_DeleteOnClose);
        dialog->setAcceptMode(QFileDialog::AcceptSave);
        dialog->setDefaultSuffix("png");
        QObject::connect(dialog, &QFileDialog::fileSelected, &window, [&](const QString &path) {
            QSaveFile file(path);
            if (!file.open(QIODevice::WriteOnly) || !canvas->pixels.save(&file, "PNG") || !file.commit())
                report("Export failed: " + file.errorString());
            else report("Exported 1024x768 PNG: " + path);
        });
        dialog->open();
#endif
    });
    addAction("Clear", QKeySequence("Ctrl+L"), [&] { canvas->clear(); });
    addAction("Reset view", QKeySequence("Ctrl+0"), [&] { canvas->pan = {}; canvas->update(); });
    auto *scale = new QComboBox;
    for (int n : {100, 125, 150, 175, 200}) scale->addItem(QString::number(n) + "%", n);
    toolbar->addWidget(scale);
    auto setScale = [&](int index) {
        const int value = scale->itemData(index).toInt();
        applyScale(value);
        QSettings().setValue("uiScalePercent", value);
        report(QString("UI scale %1%; image 1024x768 DPR=1; window DPR=%2")
            .arg(value).arg(window.devicePixelRatioF()));
    };
    int index = scale->findData(QSettings().value("uiScalePercent", 150).toInt());
    scale->setCurrentIndex(index < 0 ? 2 : index);
    QObject::connect(scale, &QComboBox::currentIndexChanged, &window, setScale);
    setScale(scale->currentIndex());
    auto *testMenu = window.menuBar()->addMenu("Tests");
    QObject::connect(testMenu->addAction("Qt dialog"), &QAction::triggered, &window, [&] {
        auto *dialog = new QMessageBox(QMessageBox::Information, "Widget dialog", "Test controls at all five scales, keyboard focus and window edges.", QMessageBox::Ok, &window);
        dialog->setAttribute(Qt::WA_DeleteOnClose);
        dialog->open();
    });
    QObject::connect(testMenu->addAction("Create OpenGL widget"), &QAction::triggered, &window, [&] {
        auto *gl = new GLProbe;
        gl->report = report;
        tabs->setCurrentIndex(tabs->addTab(gl, "OpenGL"));
        auto *timer = new QTimer(gl);
        QObject::connect(timer, &QTimer::timeout, gl, [gl] { gl->update(); });
        timer->start(33);
        report("Requested OpenGL widget; initialization and visible frame counter must be verified");
    });
    window.resize(1100, 760);
    window.show();
    if (window.windowHandle()) {
        auto safeArea = [&] {
            const QMargins margins = window.windowHandle()->safeAreaMargins();
            window.setContentsMargins(margins);
        };
        QObject::connect(window.windowHandle(), &QWindow::safeAreaMarginsChanged, &window, safeArea);
        safeArea();
    }
    report(QString("Qt %1 / %2 / native DPR %3").arg(qVersion(), QGuiApplication::platformName()).arg(window.devicePixelRatioF()));
    report("Documents: " + documents);
    report("App data: " + data);
    report("Cache: " + QStandardPaths::writableLocation(QStandardPaths::CacheLocation));
    report("Draw with Pencil; fingers pan. No .kra loader, Krita engines or resource database in this probe.");
    return app.exec();
}
