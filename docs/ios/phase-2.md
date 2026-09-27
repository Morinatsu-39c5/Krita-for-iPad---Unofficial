# 阶段 2：完整 Krita 应用已构建，待真机启动

2026-09-22，用户确认 KritaIOSProbe 已在 iPad Pro M5 真机运行，并授权继续。截图证明 Widgets 界面和画布笔迹；不把截图当作 OpenGL、倾斜、iCloud 或完整 Krita 验收证据。保持未签名构建，不创建 Git 提交。

## 已完成的依赖

目标前缀 `.deps/ios`，宿主工具 `.deps/host`，Qt 6.10.3，iPadOS 17+ ARM64。
`target-libraries.txt` 由 `verify-target-libs.py` 检查 Mach-O 的架构和 LC_BUILD_VERSION 平台；不是运行测试。

- KDE Frameworks 6.18.0：Config、WidgetsAddons、CoreAddons、Codecs、Completion、GuiAddons、ItemViews、I18n、ColorScheme。
- GNU libintl 0.23.1、PNG 1.6.50、JPEG Turbo 3.1.4.1、Expat 2.7.5、Brotli 1.2.0。
- Exiv2 0.28.8、LittleCMS 2.19 与 fast_float。
- FreeType 2.14.3（当前为无 HarfBuzz 的 bootstrap 版本）、HarfBuzz 12.3.2、Fontconfig 2.16.0、FriBidi 1.0.16、libunibreak 7.0。
- QuaZip 1.4、GSL 2.8（ampl 固定提交）；xsimd 14.1.0、Boost 1.87.0、Eigen 5.0.1、Immer 0.9.1、Zug 0.1.2、Lager 固定提交头文件。

版本参考 KDE 官方 krita-deps-management，checkout 0fd95c4efca2e5b5024121bb0ccae5b353956cd9。各 Git 依赖的实际 revision 保存于 logs/deps-*-revision.txt。

## 可复用构建入口

新 checkout 先运行 `fetch-source.sh` 和 `apply-krita-patch.sh`。

先运行阶段 1 的 build-deps.sh，再 provision-krita-tools.sh 补装 Qt QML/Quick、SVG、Core5Compat、ShaderTools 及宿主工具。
依赖按顺序逐个运行，失败时停止修复，不把缺失依赖自动视为可禁用：

```bash
./packaging/ios/build-krita-deps.sh ecm
./packaging/ios/build-krita-deps.sh host-kconfig
./packaging/ios/build-gettext.sh
# build-krita-deps.sh 分别构建：
# kconfig kwidgetsaddons kcoreaddons kcodecs kcompletion kguiaddons
# kitemviews ki18n kcolorscheme
# png expat brotli exiv2 lcms2 jpeg immer zug lager eigen
./packaging/ios/fetch-boost.sh
./packaging/ios/build-krita-deps.sh freetype
./packaging/ios/build-krita-deps.sh harfbuzz
./packaging/ios/build-krita-deps.sh unibreak
./packaging/ios/build-fontconfig.sh
./packaging/ios/build-fribidi.sh
./packaging/ios/build-krita-deps.sh quazip
./packaging/ios/build-krita-deps.sh xsimd
./packaging/ios/build-krita-deps.sh gsl
./packaging/ios/configure-krita.sh
./packaging/ios/build-krita-core.sh
./packaging/ios/build-krita-app.sh
./packaging/ios/package-krita.sh
```

Fontconfig 使用 Meson 的 iOS 交叉编译文件，Krita 本体继续使用 CMake。SDK 的 zlib 元数据从 SDK 头文件生成，不混用 Homebrew 的目标库。pkg-config 路径修复支持工作区名称中的空格。依赖安装日志保留于 logs/。

## 平台修改与限制

源码改动汇总于 `patches/ios/krita-ipados.patch`，由 `export-krita-patch.py` 导出，包括新文件，不进行暂存或提交。

| 修改 | 原因及用户影响 | 后续 |
|---|---|---|
| macOS 的 AppKit、osx.mm、包布局分支排除 IOS | iOS 不提供桌面 API；继续使用 Qt/iOS 平台能力 | 按实际编译错误逐项适配 |
| 不查找/嵌入 Python | 禁止以桌面 Python 方式运行插件 | Python 功能暂缓，资源数据导入不受此决定限制 |
| KConfig 外部迁移工具、kdialog 与 KF 帮助启动进程加保护 | Qt iOS 不提供 QProcess | 外部程序功能不可用；迁移工具暂缓 |
| KF QML 扩展关闭 | 构建最小 Widgets 依赖；不等于关闭 Krita 自己的 QML | Krita 文字工具需要的 Qt QML 单独保留 |
| TIFF 未找到时不执行 TIFF 强制检测 | 原脚本将可选库变成必需库，且包含运行检测 | TIFF 恢复时补交叉检测；PSD 插件已参与编译，读写待验证 |
| Exiv2 版本号与 MyPaint 缺失检测修复 | 新版版本宏有 U 后缀；可选库缺失不能无条件读取 config.h | 不改变已有平台功能 |
| 静态库、Qt 静态插件查询和自动工厂导入 | iPadOS 内置可执行插件须随包交付 | 编译链接通过，尚未证明真机笔刷可用 |
| UI 调试文字复制回退到剪贴板 | Qt iOS 无外部进程；不影响键盘快捷键 | 桌面行为保留 |
| 关闭桌面更新器；FFmpeg 外部进程明确返回失败 | iOS 不支持这些进程模式 | 视频功能后续可用进程内后端恢复 |
| OpenGL ES 与触控板平台判断 | 用 Qt 功能宏识别 GLES，排除桌面 GL 枚举及 macOS 触控板分支 | 编译通过，待真机渲染验证 |
| Bundle plist 和资源查找根目录 | 应用名、iPad 横屏、可配置签名标识 | 资源打包检查通过，个人签名与启动待验收 |

未构建的可选库包括 MyPaint、TIFF、OpenEXR、OpenColorIO、WebP、HEIF、JPEG XL、OpenJPEG、Poppler、FFTW、视频及 RAW 相关依赖；相应功能目前不能宣称支持。GSL 在实际源码编译阶段证实必需，现已补齐。它的 iOS 交叉配置使用 Darwin ARM64 的 IEEE/stdio 能力假设，并用目标编译器检查 char 符号；未将这些检查声称为设备运行测试。先完成基础绘画，再按原任务要求逐项恢复。

## 实际验证结果（2026-09-23）

完整 CMake 配置、源码编译和最终链接均已通过。147 个正式 Krita 插件工厂静态导入（排除测试插件），另显式导入 Krita QML 插件。kritaimage、kritaui、工具、内置笔刷和格式插件已编译；194 个静态归档通过 ARM64 / iOS platform 2 检查，见 `krita-core-libraries.txt`。

成功输出 `.build/krita-ios-install/krita.app`（455,444,380 字节）及 `.build/Krita-iPadOS-unsigned.ipa`（146,165,071 字节）。应用仅动态依赖 iOS 系统库，4 个默认资源包 ZIP CRC 检查通过，IPA 的结构、CRC 与 plist 检查通过。codesign 确认应用未签名。检查结果及 SHA256 见 `krita-app-validation.txt`。

构建日志为 `logs/krita-app-build.log` 与 `logs/krita-app-final-build.log`；打包日志为 `logs/krita-package.log`。打包时发现 macOS Spotlight/Quick Look 安装规则误覆盖 iOS，现已用 `APPLE AND NOT IOS` 排除。完整安装所需但未被主可执行目标引用的 libkis、exifcommon 也纳入构建脚本。

**阶段 2 尚未完成真机主窗口验收。** 已通过真机测试的仍只有阶段 1 探针。完整 Krita 的主窗口启动、画布渲染、现有 GUI 缩放泛化、Pencil/Files 接入与 .kra 保存恢复仍需验证。

## 完整应用复现与验收边界

完整应用的构建入口是 `configure-krita.sh` → `build-krita-app.sh` → `package-krita.sh`。
实验性 Xcode 工程入口为 `configure-krita-xcode.sh`，目录 `.build/krita-ios-xcode`；默认关闭签名。本机尚未成功生成完整工程，不能将其作为可用交付物。
`KRITA_IOS_BUNDLE_ID`、`KRITA_IOS_TEAM_ID` 由配置脚本传给 CMake，不保存个人证书。
Xcode 多配置构建可使用 `KRITA_BUILD_DIR` 和 `KRITA_BUILD_CONFIG` 选择目录及配置；打包必须在构建完成后执行。

已生成的待测试应用位置为 `.build/krita-ios-install/krita.app`。构建目录内的 `.app` 尚未复制完整资源，不用于安装验收。
`verify-krita-app.py` 检查实体 iOS ARM64、系统动态依赖、默认资源、字体配置和 bundle 内无外部符号链接；这些静态检查不能证明应用启动成功。

静态链接还要求将原来位于独立插件中的同名内部类区分命名，JPEG/ORA/heightmap 共用转换代码改为各自共用一个静态库，头文件函数使用 inline。
宽色域选择器和 RGBE 导入插件也改用统一的 `kis_add_library` 入口，以保证参与静态注册。WebP 的同类入口已修复，当前未启用 WebP 依赖。
PNG 明确选择 `libpng16.a`，避免 CMake 优先选中旧安装目录中的动态 framework。

真机首轮只验收：启动到原版主窗口、默认资源成功加载、新建画布。随后验证连续 Pencil 笔迹、压感/倾斜、图层/撤销和 .kra 保存恢复。
现有 Android 动态缩放代码位于 `KisAndroidScaling`，包含 JNI 对话框与屏幕密度处理；尚未泛化到完整 iPad 应用。探针的 150% GUI 缩放、Files 导出桥接不能自动视为完整 Krita 已具备。

### Xcode 生成器的独立阻塞

2026-09-23：允许 Xcode 访问正常开发缓存后，编译器识别通过；随后在 Krita 根 `CMakeLists.txt` 的 `check_cxx_symbol_exists(QT_HAS_ENTER_LEAVE_PATCH ...)` 配置检测处失败。
CMake 报错为 `$<TARGET_OBJECTS:Qt6::Gui_resources_1>` 无法在 try_compile 导出的目标中求值，随后提示目标不存在。
日志为 `logs/krita-xcode-configure.log`。这是 Xcode 生成器下 Qt 静态资源目标导出问题；当前可用完整应用构建采用 Ninja，不伪造这些特性检测结果。
