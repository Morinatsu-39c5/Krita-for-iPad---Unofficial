# Krita iPadOS 移植工程概况

更新日期：2026-09-27。本文描述本地工作区的实际状态，不代表完整移植已经验收。

## 1. 当前结论

工程已从独立 Qt Widgets 探针推进到 Krita 主程序：完成 iPadOS ARM64 编译、静态插件链接、未签名应用打包，并生成可签名构建和真机运行的完整 Xcode 工程。

2026-09-23 的资源数据库启动问题已经完成真机闭环：用户确认 SQL、数据库和默认 bundle 错误消失，主窗口可显示且第二次启动正常。随后发现新建文档时应用退出。2026-09-24 的报告先证明约 0.55 秒的 UIKit 主线程卡顿终止；拆分初始化后又暴露出颜色三角形顶点 NaN 和颜色历史空文档两处崩溃，均已依据设备 `.ips` 修复。进入画布后的另两次闪退进一步定位到 Qt iOS 对 Apple Pencil `UITouch` 的悬空指针，现已加入 iOS 触控生命周期保护。新发现的保存弹窗无响应来自 iOS 上同步 `QFileDialog::exec()`；`.kra` 保存现绕过该模态循环，直接写入 Files 可见的应用 `Documents`。详见[独立评审](project-review-2026-09-23.md)、[修复计划](repair-plan-2026-09-23.md)、[修复进度](repair-progress-2026-09-24.md)、[原启动问题记录](device-startup-issues-2026-09-23.md)、[新建文档卡顿记录](new-document-runloop-hang-2026-09-24.md)、[画布触控闪退与卡顿记录](canvas-touch-crash-and-performance-2026-09-24.md)和[沙盒保存记录](files-save-sandbox-2026-09-24.md)。

新的未签名 IPA 已生成；Xcode Debug 与 Release 应用均已用 Team ID `<personal-team-id>` 构建。Release 应用使用 `-O3` 和 `NDEBUG`，已完成签名、实体 iPad 安装及启动。新建文档修复和触控保护分别完成 180 秒实机观察；后一次测试中 UIKit 实际触发了“部分触控被取消”的危险路径，应用仍保持运行，同一时段没有生成新 `.ips`。用户随后测试 Release 画布，确认卡顿与偶发闪退看起来已经解决。输入版 Debug 在真机上再次出现卡顿，因此最新输入改动改用 Release 构建：Pencil 双击切换当前笔刷/橡皮，Pencil Pro 捏压打开轮盘，非文本触摸增加全局输入法守卫。最新 Release 已签名安装并启动，尚待人工确认行为和流畅度。所有代码修改保留在本地，不暂存、不提交 Git。

2026-09-26 用户报告关闭确认偶发失去响应，以及设置里的 Apple 滚轮不可操作。已确认键盘保护与 Qt 原生 picker 共用 inputView 的冲突，现对 picker 放行；关闭确认改为异步 Qt Widgets 对话框，笔画和保存等待使用定时检查。生产回调的宿主 Qt 自动回归通过，签名 Release 构建、应用门禁及 iPad 安装、启动通过（PID 6648，复查仍在运行，近期崩溃列表为空）；具体弹窗触摸行为仍待人工复测。详见[关闭确认与系统滚轮修复](popup-and-picker-repair-2026-09-26.md)。

2026-09-26 用户报告只有部分按钮为中文。已确认 Krita 的 `.mo` 目录注册太晚导致 KI18n 缓存首次查找失败；提前注册后正文恢复。三语言真机回归又发现静态 gettext 的探测漏掉 CoreFoundation/iconv，使 KI18n 缺少语言缓存刷新。依赖探测补齐后重新构建，简体、繁体、英语菜单和设置正文的真机查询与 catalog 逐项一致；最终签名 Release 已安装并以普通方式启动（PID 6698）。详见[正文翻译与简繁切换修复](localization-repair-2026-09-27.md)。

## 2. 目标与约束

- 将 KDE Krita 移植到 11 英寸 iPad Pro M5，目标 ARM64 实体设备，优先横屏。
- 保留现有 Qt Widgets 菜单、工具栏、Docker 和画布，不用 SwiftUI/UIKit 重写前端。
- GUI 默认 150%，可配置；优先泛化现有 Android 动态缩放，不改变图像像素和笔刷坐标。
- 支持 Apple Pencil 基础绘画、压力与倾斜，分离手指手势和笔迹。
- 支持通过 Files 打开、保存文档及导入 .kpp、.bundle、.abr 等非可执行资源，复用 Krita 资源数据库。
- 内置引擎和插件随应用静态编译；个人签名安装优先，暂不处理 App Store 发布。
- Python、外部进程、外部二进制插件等桌面功能可以暂缓，需记录影响。

## 3. 环境与源码基线

| 项目 | 本工作区记录 |
|---|---|
| 工作区 | `<workspace>` |
| 宿主 | macOS 15.7.8 / ARM64 |
| Xcode / SDK | Xcode 26.3 (17C529) / iPhoneOS SDK 26.2 |
| 构建工具 | CMake 4.4.3、Ninja |
| Qt | 6.10.3，官方 macOS 宿主工具和 iOS kit |
| 目标 | iPadOS 17.0+，ARM64 真机 |
| Krita | KDE/krita，6.1.0-prealpha |
| 固定源码提交 | `3a9b5ef03f8312b6f630fc5d475e1692598e8719` |
| 依赖版本参考 | krita-deps-management，`0fd95c4efca2e5b5024121bb0ccae5b353956cd9` |
| 默认完整应用标识 | `org.example.krita`，可配置 |
| 签名状态 | Ninja IPA 保持未签名；Xcode Debug 与 Release 应用已用 Team ID `<personal-team-id>` 签名并完成真机安装、启动 |

## 4. 阶段进度与验收边界

| 阶段 | 已完成 | 尚未完成或验证 |
|---|---|---|
| 0：环境 | 已实际生成 iPadOS 二进制 | 无环境级编译阻塞 |
| 1：Widgets 探针 | Xcode 工程、未签名应用、宿主自动测试；用户确认真机可运行，截图有界面和笔迹 | 不将截图作为 GLES、倾斜、iCloud、全部外设输入的验收 |
| 2：完整核心与应用 | 核心、主界面、插件编译链接；14 组静态 qrc 通用初始化；Ninja 未签名应用验证；完整 Xcode 工程的 Debug/Release 已签名构建、安装、启动；真机主窗口与第二次启动通过 | Release 长时间运行仍需继续回归 |
| 3：基本绘画 | 原有画布、工具、笔刷等源码参与构建；新建文档的主线程卡顿、颜色选择器 NaN、颜色历史空指针和 Qt Pencil 触控悬空指针均已修复；触控压力测试 180 秒无崩溃、无新 `.ips`；`.kra` 首次保存已改为直接写入 Files 可见的 `Documents`；Pencil 双击切换橡皮、Pencil Pro 捏压轮盘、单指轮盘解绑及全局输入法守卫已完成 Release 编译安装 | 最新 Release 的画布流畅度和新输入行为、连续第二次新建、压感/倾斜、图层、撤销、.kra 保存重开和长时间绘画仍需验证 |
| 语言 | catalog 打包及声明完成；提前注册目录、gettext 语言缓存刷新修复完成；真实 KI18n 简繁中文/英语菜单与设置正文回归、真机报告门禁通过 | 完整界面布局、手动语言选择后重启及系统语言切换仍待验证；catalog 未翻译词条可能显示英语 |
| 4：资源导入 | 保留原资源系统及默认资源包 | Files 导入 .kpp/.bundle/.abr、重启持久化与实际使用未验收 |
| 5：功能恢复优化 | 部分格式和引擎已参与编译 | 可选依赖恢复、复杂格式兼容、动画、内存和渲染性能仍待后续推进 |

## 5. 目录与产物

以下路径均相对工作区根目录。

| 路径 | 用途 |
|---|---|
| `upstream/krita/` | 固定基线的 Krita 源码及未提交移植修改 |
| `packaging/ios/` | 获取源码、依赖构建、配置、构建、打包、检查脚本 |
| `packaging/ios/probe/` | 独立 Qt Widgets 探针源码 |
| `upstream/krita/packaging/ios/` | 完整应用的 CMake bundle 配置、Info.plist、字体配置等 |
| `patches/ios/krita-ipados.patch` | 已导出的 Krita 源码改动，包含新增文件；不是 Git 提交 |
| `.qt/6.10.3/` | macOS 和 iOS Qt kit |
| `.deps/src/`、`.deps/host/`、`.deps/ios/` | 依赖源码、宿主工具、iOS 目标依赖 |
| `.build/krita-ios/`、`.build/krita-ios-install/` | 可由现有脚本重新生成的 Ninja 构建和安装暂存目录；已于 2026-09-25 清理 |
| `.build/Krita-iPadOS-unsigned.ipa` | 2026-09-24 的未签名 Debug IPA，包含 Pencil 橡皮/轮盘、输入法、沙盒保存、语言资源和 QUIView 方法交换修复；不含 2026-09-26 弹窗修复，163,312,825 bytes；SHA256 `4ab24601de1996018ead2ae244745c146afc9152011a919b52067ef88727edde` |
| `.build/ios-probe/`、`.build/macos-probe/` | 可由探针脚本重新生成的构建目录；已于 2026-09-25 清理 |
| `.build/Krita-iPadOS-Release-signed.ipa` | 2026-09-27 最新签名 Release IPA，包含关闭确认、系统滚轮与正文翻译/简繁切换修复；118,793,585 bytes，SHA256 `5b5b03eb0789465166a446df473a9df8714122f842356d71ed5047a34d633185` |
| `.build/krita-ios-xcode/krita.xcodeproj` | 已验证的完整 Krita Xcode 工程，主 scheme 为 `krita` |
| `.build/krita-ios-xcode/bin/Debug/` | 已被 Release 版本取代，于 2026-09-25 清理；需要时可由 Xcode 重建 |
| `.build/krita-ios-xcode/bin/Release/krita.app` | Xcode 直接生成的最新已签名 ARM64 Release 应用，`-O3`、`NDEBUG`，包含 Pencil 橡皮切换、picker 保护、异步关闭与正文翻译修复；已安装并普通启动（PID 6698），具体弹窗行为仍待用户测试 |
| `docs/ios/` | 环境、依赖、构建、验收及问题文档 |
| `logs/` | 配置、编译、打包和检查日志 |

2026-09-25 清理了旧 Ninja、Debug、探针、依赖编译暂存和 Xcode 安装暂存产物，工作区从约 45 GB 降至约 18.5 GB。Qt kit、依赖源码和安装前缀、完整 Xcode 工程、Release 增量编译数据、最新签名 Release 应用、IPA、补丁、文档与日志均保留。当前 IPA 与已实机测试的 Xcode 签名应用来自同一套修复源码；完整绘画版本仍需完成 Pencil 压感/倾斜、图层、保存恢复和长时间稳定性验收。

## 6. 已完成的技术工作

- 区分 iOS 与 macOS，排除 AppKit、macOS Spotlight/Quick Look 扩展等桌面构建和安装分支。
- 将 Krita 库及内置模块转为 iOS 静态构建，适配 Qt 静态插件查询，生成 147 个正式 Krita 插件工厂导入，并导入 Krita QML 与必要 Qt 插件。
- 处理静态链接下的同名工厂、内部类和重复转换器代码问题。
- 编译 kritaimage、kritaui、现有 OpenGL ES 画布和输入层；修正 GLES 功能宏和桌面触控板条件分支。
- 为应用补充 iPad plist、横屏设置、图标、字体配置及 bundle 资源查找路径。
- 为 Qt iOS 不支持的外部进程路径增加保护，关闭桌面更新器及 Python 相关构建路径。
- 使用静态 PNG，避免最终程序依赖未随包交付的 PNG framework。
- 提供可复用构建脚本、补丁导出与应用检查入口。
- 为 iOS 建立静态 qrc 注册表，自动生成初始化代码与 14 项资源清单，在数据库初始化前执行运行时哨兵检查。
- 加固应用与 IPA 门禁，支持优化模式下的显式失败、签名状态、静态资源符号和 IPA 逐文件复验。
- 修复 Xcode `try_compile` 对 Qt 静态资源 target 的传播问题，并让 Xcode 主 target 自动安装运行时数据。
- 针对 iPadOS UIKit HangTracer，将新建文档的欢迎页切换、视图创建和视图挂载拆到三个主线程事件，并用 Qt context 与 `QPointer` 保护异步阶段。
- 修复高级颜色选择器三角形顶点的零除与 NaN，并限制传给 Qt 的 HSV 分量。
- 修复分阶段画布挂载时颜色历史 Docker 通过 ViewManager 取得空文档的问题，改从画布自己的 View 取得文档并保护可空对象。
- 为 Qt 6.10.3 iOS 的 `QUIView` 加入 Pencil `UITouch` 生命周期保护，清除异常 UIKit 取消序列留下的过期指针，避免下一次触控在 `containsObject:` 中访问已释放对象。
- 将 iOS 的新文档保存和“另存为”固定到当前沙盒的 Files 可见 `Documents`，自动生成不覆盖的 `.kra` 文件名，并绕过会卡住触控的同步文件对话框。
- 通过 `UIPencilInteraction` 将 Apple Pencil 笔杆双击接到 `erase_action`，Pencil Pro 捏压接到现有轮盘，并在 iOS 输入配置中移除单指触摸轮盘绑定。
- 让 iOS 画布输入法只在文本工具的文本模式启用，离开文本模式时清理预编辑并收起键盘；全局守卫在非文本焦点/触摸后再次隐藏输入法，普通图层触摸不再隐式进入改名。
- 构建并打包 859 个语言文件；在正式应用构造之前注册 `.mo` 目录，修复静态 gettext 检测以支持语言缓存刷新；门禁可比较真机 KI18n 简繁中文/英语报告与 catalog。

以上是源码及构建层面的完成情况，不等同于相关功能已在完整应用中运行通过。

## 7. 依赖与功能范围

已构建的主要依赖包括 KDE Frameworks 6.18、libintl、PNG、JPEG Turbo、Expat、Brotli、Exiv2、LittleCMS、FreeType、HarfBuzz、Fontconfig、FriBidi、libunibreak、QuaZip、GSL，以及 Boost、Eigen、Immer、Zug、Lager、xsimd 等。具体版本与构建顺序见[阶段 2 记录](phase-2.md)。

FreeType 当前仍为未启用 HarfBuzz 的 bootstrap 构建。MyPaint、TIFF、OpenEXR、OpenColorIO、WebP、HEIF、JPEG XL、OpenJPEG、Poppler、FFTW、KSeExpr、视频和 RAW 相关依赖尚未全部构建，相关功能不能宣称支持。PSD 插件已参与编译，但实际读写及兼容性未验收。

完整应用尚未接入默认 150% 可配置 GUI 缩放；现有 `KisAndroidScaling` 包含 JNI 和屏幕密度处理，需进一步泛化。探针中的缩放和 Files 桥接不能自动视为完整 Krita 已具备。

## 8. 构建入口与现有验证

在依赖已准备好的工作区中，完整应用的入口为：

```bash
./packaging/ios/configure-krita.sh
./packaging/ios/build-krita-app.sh
./packaging/ios/package-krita.sh
```

这些命令已在 2026-09-24 使用当前源码重新执行并通过。

`build-krita-app.sh` 构建主程序及安装所需的 libkis、exifcommon；`package-krita.sh` 复制资源并生成未签名 IPA。依赖不是由单个 `build-deps.sh` 全部构建：该脚本主要服务探针 Qt 环境，完整依赖步骤见阶段 2 文档。

| 检查 | 结果及限制 |
|---|---|
| 最终编译链接 | 通过 |
| 194 个静态归档架构/平台检查 | ARM64 / iOS platform 2，通过；不是运行测试 |
| 应用动态依赖 | 仅系统库，通过 |
| 4 个默认资源包、IPA 完整性 | 通过 |
| 源码补丁及脚本语法检查 | 已通过当时检查 |
| 完整应用真机启动 | 用户已确认 SQL/数据库/bundle 错误消失、主窗口显示、第二次启动正常；最新 Release 输入构建已重装并启动，无启动期新 `.ips` |
| 新建文档与画布触控 | 已依据设备报告修复 UIKit 卡顿、颜色选择器 NaN、颜色历史空指针和 Qt Pencil 触控悬空指针；两轮 180 秒实机观察无新 `.ips`；用户确认 Release 画布卡顿与偶发闪退看起来已解决 |
| Release 优化应用 | `-O3`、`NDEBUG`、ARM64 iOS device、签名、仅系统动态依赖、4 个默认 bundle、14 组 qrc 与触控保护符号均通过；已安装、启动和实机绘画 |
| 内嵌静态 qrc 资源 | 14 组要求资源的初始化符号与 qrc 源哨兵全部通过 Ninja/Xcode 应用检查 |
| 完整 Xcode 工程生成 | 通过；`.build/krita-ios-xcode/krita.xcodeproj` 的 `krita` scheme 已签名 ARM64 device 构建通过 |
| 历史输入与语言 Xcode Debug 构建（2026-09-24） | `BUILD SUCCEEDED`；1,466 个文件、492,948,588 bytes；859 个语言文件；应用门禁通过。主机严格证书链检查返回 `CSSMERR_TP_NOT_TRUSTED`，实体 iPad 已接受签名应用安装与启动；当前使用 Release |
| 最新正文翻译与简繁切换 Release（2026-09-27） | `BUILD SUCCEEDED`；宿主真实 KI18n 回归及三语言真机报告逐项比较通过；签名 IPA 校验、覆盖安装、普通启动通过，PID 6698 复查仍在运行 |
| Xcode 签名范围 | 最终应用签名；静态库和插件不签名，`krita_colorspaces_extensions` 等中间 target 不再要求 Development Team |
| Xcode 直接运行资源 | 构建后自动安装 `krita` 数据组件；已签名 `.app` 已由 `devicectl` 安装并在实体 iPad 启动 |

产物校验记录见 [krita-app-validation.txt](krita-app-validation.txt)。静态检查仍会标注 “device launch: NOT VERIFIED”，因为检查器本身不操作实体设备；Debug 的 180 秒触控观察、Release 的安装启动及用户画布测试另有设备结果支持。

## 9. 后续工作顺序

1. 在已安装的最新 Release 上验证手指不弹轮盘、Pencil 双击切换橡皮、Pencil Pro 捏压轮盘、非文本操作不弹键盘，以及显式改名和文本工具仍可输入。
2. 验证简体/繁体中文切换、完全退出重启和主要菜单/Docker/对话框翻译。
3. 真机验证 `.kra` 保存、Files 可见性、关闭重开、图层与笔迹一致性。
4. 延长 Release 绘画回归，覆盖大画布、复杂笔刷、后台恢复和多次抬笔重落。
5. 验证 Pencil 压感/倾斜和图层撤销。
6. 泛化 GUI 缩放，接入异步 Files 外部位置导入导出，再逐项恢复可选功能和开展性能优化。

## 10. 文档导航

- [后续修复计划（依据独立评审）](repair-plan-2026-09-23.md)
- [2026-09-24 修复进度与新产物](repair-progress-2026-09-24.md)
- [2026-09-24 新建文档卡顿退出分析与修复](new-document-runloop-hang-2026-09-24.md)
- [2026-09-24 画布触控闪退与卡顿分析](canvas-touch-crash-and-performance-2026-09-24.md)
- [2026-09-24 沙盒保存路径与弹窗无响应修复](files-save-sandbox-2026-09-24.md)
- [2026-09-24 Pencil 轮盘手势与输入法修复计划](input-gesture-and-keyboard-plan-2026-09-24.md)
- [2026-09-27 正文翻译与简繁切换修复](localization-repair-2026-09-27.md)
- [工作区独立评审](project-review-2026-09-23.md)
- [最新真机问题及 Xcode 状态](device-startup-issues-2026-09-23.md)
- [阶段 0–1：探针报告](phase-0-1.md)
- [阶段 2：依赖、平台改动和构建记录](phase-2.md)
- [构建与个人签名说明](build.md)
- [依赖分析](dependencies.md)
- [完整应用真机验收表](krita-device-checklist.md)
- [产物静态检查记录](krita-app-validation.txt)

早期文档中“待真机启动”的历史状态，以本概况及最新真机问题记录为准。
