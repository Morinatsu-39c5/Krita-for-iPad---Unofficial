# 源码依赖与平台调查

基线：KDE/krita 主线 `3a9b5ef03f8312b6f630fc5d475e1692598e8719`。

2026-09-27 的依赖修复补充：KI18n 6.18.0 的静态 GNU gettext 检测需要同时链接 CoreFoundation 与 iconv，否则错误关闭 `_nl_msg_cat_cntr` 缓存刷新。已有 `patches/ios/dependencies/ki18n/0001-ios-static-gettext-link-probe.patch`；构建脚本自动应用，已有失败缓存用 `build-krita-deps.sh ki18n -U HAVE_NL_MSG_CAT_CNTR` 重新检测。详见[正文翻译与简繁切换修复](localization-repair-2026-09-27.md)。下方分类保留最初调查时的阶段状态，当前总体状态见[工程概况](project-overview.md)。
已阅读 README、README.android.md、README.packagers.md、HACKING、主 CMakeLists.txt 及相关平台实现；checkout 内未发现 AGENTS.md。

`inventory-deps.py` 从实际源码提取 105 条 CMake package 声明，见 [完整声明清单](dependency-declarations.md)。清单保留必需/可选标记、变量及源码位置，包含平台与 vendor/test 条件；它不是已解析的 iOS 依赖闭包。下表是进入阶段 2 前的分类，除 Qt 探针所用库外，交叉编译可行性尚未通过构建验证。

| 类别 | 依赖与源码线索 | 状态/处理 |
| --- | --- | --- |
| 1. Qt 官方 iOS 包 | Core、Gui、Widgets、Xml、Network、Concurrent、Sql、Test、OpenGL、OpenGLWidgets（主CMake 558–610）；Svg、SvgWidgets、Core5Compat 是额外模块 | 本轮只安装 qtbase；Core/Gui/Widgets/OpenGLWidgets 已链接成功，其他模块和 SQLite 资源数据库尚未验收。PrintSupport 不能照搬桌面要求 |
| 2. CMake 交叉编译候选 | PNG≥1.6、ZLIB、JPEG/libjpeg-turbo、LCMS2≥2.4、Eigen3≥3.3（优先5）、Boost≥1.69、Immer/Zug/Lager、LibExiv2≥0.16、Freetype≥2.11、HarfBuzz≥4（Qt6分支），主CMake 1158–1635 | 核心依赖须按 ARM64/iOS 编译或使用适用头文件；不能链接 Homebrew macOS 库。Qt 内置图像/字体库不等于 Krita 所需独立开发包。libunibreak、Fontconfig 需另核对现有构建方式及沙盒字体访问 |
| 3. 关闭动态发现/改静态注册 | KF6 Config、WidgetsAddons、Completion、CoreAddons、GuiAddons、I18n、ItemViews、ColorScheme；Krita 插件工厂，KoJsonTrader/KoPluginLoader | 不仅需要 Q_IMPORT_PLUGIN，还必须改 Krita 插件查询/注册路径，使 JSON 元数据和 paintop 工厂可枚举；打包翻译与资源；不能只设置 BUILD_SHARED_LIBS=OFF |
| 4. 平台适配 | KisAndroidScaling、KisMainWindow、KisApplication、KisFileDialog、输入管理、资源路径、字体发现、配置与恢复、packaging/macos | Android 缩放依赖 patched QPlatformScreen::setDensityAdjustment、JNI 和 Android 对话框，源码 CMake 764 附近有说明；先分离共用部分，保留 Android 行为。iOS 使用独立文档选择器边界和应用沙盒 |
| 5. 延后/可选组件 | GSL、WebP、KSeExpr、OpenEXR、TIFF、GIF、HEIF、OpenJPEG、JPEGXL、FFTW3、OpenColorIO、SIP/PyQt/Python、Mlt7/SDL2、LibMyPaint、xsimd、Poppler、QUAZIP、KDcraw；平台 X11/Wayland/DBus/Crash/unwindstack | 能否不启用须逐项检查调用依赖；LibMyPaint 影响 MyPaint 引擎，不能当成普通资源问题。PSD 是后续格式恢复目标，不是一个可凭包名推断的独立依赖 |
| 6. 当前阶段门槛/预计阻塞 | 主CMake 100附近 APPLE 无条件引入 macOS packaging 和 -mmacosx-version-min；PrintSupport 必需；Fontconfig 必需；Qt6 私有头文件与自定义补丁；桌面平台插件；动态插件发现 | 是源码审查发现的待修项，尚未运行完整 Krita iOS 配置，因此不冒称是“实际构建首错”。当前真正完成的是探针构建；签名和真机验收待用户配置后执行 |

Qt6 构建需 `-DBUILD_WITH_QT6=ON -DALLOW_UNSTABLE=QT6`，主线仍默认 Qt5。后续应将 `APPLE` 下的 macOS 特定行为收窄为 `APPLE AND NOT IOS`；Objective-C++ 语言启用等可共享的行为不应一概排除 iOS。

## 画布与输入

已找到 `libs/ui/opengl/kis_opengl_canvas2.{h,cpp}` 的 QOpenGLWidget 和 `libs/ui/canvas` 中的栅格画布代码。没有从这一轮检索中确认可直接切换的 QRhiWidget/Metal 画布，因此不预先承诺 RHI 路线。Qt 官方 iOS 包和系统 OpenGLES 框架已被探针链接；下一步是真机运行 GLProbe，再评估 Krita 实际着色器、颜色管理和画布。

输入应复用 `libs/ui/input/kis_input_manager.cpp`、`KisInputEventsEater.cpp`、`kis_tablet_debugger.cpp` 的 tablet 路径。当前仅实现探针观测；是否需要 UIKit Pencil 桥接须由真实事件结果决定。

## 未来禁用项登记（本轮未实施）

| 候选项 | 原因及影响 | 恢复条件/位置 |
| --- | --- | --- |
| Python/SIP/PyQt | 初期不带脚本执行环境，Python 插件不可用；不影响数据资源导入 | 移植解释器并静态/内嵌打包后重评；plugins/CMakeLists.txt 的 HAVE_PYQT/HAVE_SIP/HAVE_PYTHONLIBS 条件及主CMake 1336附近；尚无本轮新增统一禁用选项 |
| 外部二进制插件 | 不能沿用任意运行时库加载；外部可执行扩展不可用 | 将可用内置插件编入 app 并增加注册机制；libs/koplugin/KoJsonTrader.cpp、KoPluginLoader.cpp |
| DBus/X11/Wayland/桌面平台扩展 | iOS 不具备这些桌面服务；相关集成不可用 | 平台隔离，不在 iOS 恢复桌面服务；主CMake 920–939、plugins/platforms |
| PrintSupport/扫描/桌面 Shell | 需要不同平台实现；初期无法打印、扫描或调用桌面 Shell | 单独审查使用点、可选 AirPrint 桥接；主CMake Qt REQUIRED PrintSupport 及各调用处；未添加虚假开关 |
| G’MIC/外部进程 | 外部执行模式不适用；G’MIC 功能暂缺 | 核对内嵌静态实现与依赖；3rdparty_plugins、plugins/extensions/qmic、README.packagers.md |
| 视频/MLT/SDL、外部FFmpeg | 视频导入导出与进程工作流复杂；动画交付推迟 | 嵌入式编码器和内存预算验证后逐项恢复；主CMake Mlt7/SDL2、libs/ui/animation |
| 更新通知 | 个人签名无桌面更新流程 | 后续可设计适用流程；现有 `ENABLE_UPDATERS=OFF` |
| 桌面全局快捷键 | iOS 无对应桌面全局控制；应用内外接键盘快捷键仍应保留 | 平台调用审查后隔离；不应关闭所有 QAction 快捷键 |

本轮探针不包含这些组件，未通过删除或连续禁用功能来掩盖 Krita 编译问题。

## 上游参考

- [Krita 构建说明](https://docs.krita.org/en/untranslatable_pages/building_krita.html)
- [Qt 6.10 iOS 配置](https://doc.qt.io/qt-6.10/ios.html)
- [Qt 6.10.3 原生文件对话框](https://github.com/qt/qtbase/blob/v6.10.3/src/plugins/platforms/ios/qiosfiledialog.mm)
- [Qt 6.10.3 文档选择器复制模式](https://github.com/qt/qtbase/blob/v6.10.3/src/plugins/platforms/ios/qiosdocumentpickercontroller.mm)
- MR !2836 网页访问被403拒绝；已直接审查当前源码中的已存在实现，没有把无法访问的MR内容作为事实依据。
