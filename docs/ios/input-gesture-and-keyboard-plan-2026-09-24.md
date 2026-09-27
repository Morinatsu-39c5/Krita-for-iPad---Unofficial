# Pencil 橡皮/轮盘手势、输入法与语言修复记录

更新日期：2026-09-24  
状态：源码实现、ARM64 iOS Debug 编译、应用检查、未签名 IPA 打包、签名 Xcode Release 构建、实体 iPad 安装和启动均已完成；具体输入行为和画布流畅度仍待人工验证。所有修改保持未暂存、未提交。

## 1. 问题与目标

本轮处理三个相关问题：

1. Apple Pencil 笔杆双击应直接切换当前笔刷与橡皮模式；Pencil Pro 捏压唤起轮盘；手指触摸画布不应唤起轮盘。
2. 操作图层、Docker 和画布等非文本界面时，不应误唤起软键盘或 Scribble；显式改名和文本工具仍需正常输入。
3. 应用包此前没有 Krita 翻译目录，界面只有英语；iOS 包需要包含 Krita 与 KDE Frameworks 的本地化资源。

“Pencil 手势”通过 UIKit 接入笔杆双击和 Apple Pencil Pro 捏压。双击触发 Krita 自带的 `erase_action`，捏压只在开始阶段触发一次轮盘，避免一次连续手势反复开关。

## 2. 原因确认

### 2.1 单指触摸会打开轮盘

默认输入配置 `kritadefault.profile` 的 `[Show Popup Widget]` 同时包含右键和单指触摸绑定。单指触摸通过 `KisTouchShortcut` 进入 `KisPopupWidgetAction::end()`，最终显示 `KisPopupPalette`。Qt 6.10.3 没有把 Pencil 笔杆双击和捏压暴露给 Krita 的输入配置层，需要从 UIKit 的 `UIPencilInteractionDelegate` 接入。

### 2.2 非文本操作会唤起输入法

OpenGL 与 QPainter 两个画布实现此前都无条件设置 `Qt::WA_InputMethodEnabled = true`。图层树 `NodeView` 也允许 Qt 的默认触摸或双击编辑触发器创建 `QLineEdit`。这会让普通画布焦点或图层操作被 iPadOS 识别为文本输入意图。

### 2.3 只有英语

源码含 `po/zh_CN/krita.po`、`po/zh_TW/krita.po` 等翻译，但此前只构建 `krita` target，没有构建 `pofiles`/`tsfiles`，安装后的 `share/locale` 为空。Xcode 的应用组件安装也不会自动复制无 component 的 ki18n 规则。静态 KDE Frameworks 的 `.mo`/`.qm` 位于 `.deps/ios/share/locale`，此前同样没有进入 app。

## 3. 已实施修改

### 3.1 Apple Pencil 橡皮和轮盘入口

- 在 Qt iOS 的 `QUIView` 上安装 `UIPencilInteraction`，delegate 与 interaction 通过关联对象跟随视图生命周期。
- 支持 `pencilInteractionDidTap:`，并在 iPadOS 17.5+ 支持 tap 和带 hover 位置的 squeeze。
- Pencil tap/双击通过 C++ 桥触发 Krita 自带的 `erase_action`，保持当前笔刷，只切换橡皮合成模式，并同步工具栏的橡皮状态。
- squeeze 仅在 `UIPencilInteractionPhaseBegan` 调用一次。
- 优先使用 hover 位置；没有 hover 时使用最近一次 Pencil 触点；仍不可用时回退到画布中心。
- UIKit 回调通过独立 C++ 桥进入 `KisInputManager::togglePopupWidgetAt()`，复用当前工具已有的 `KisPopupWidgetInterface`。
- iOS 加载输入配置时跳过 `Show Popup Widget` 的触摸绑定；右键绑定和非 iOS 平台保持原行为。
- 原有 Qt 6.10.3 Pencil `UITouch` 生命周期保护继续保留。

涉及文件：

- `upstream/krita/krita/krita_ios_touch_guard.mm`
- `upstream/krita/krita/krita_ios_pencil_bridge.cpp`
- `upstream/krita/libs/ui/input/kis_input_manager.h`
- `upstream/krita/libs/ui/input/kis_input_manager.cpp`

### 3.2 输入法与图层编辑

- iOS 的 OpenGL 和 QPainter 画布默认关闭 `WA_InputMethodEnabled`。
- `slotToolChanged()` 与 `slotTextModeChanged()` 根据 `tool->isInTextMode()` 动态开关输入法。
- 离开文本模式时调用输入法 reset/hide，清理预编辑并收起输入面板。
- 增加 iOS 全局焦点/触摸守卫；触摸画布、Docker、图层和其他非文本控件后，在 Qt 焦点处理完成时再次 reset/hide，避免输入面板被重新唤起。
- 数值微调框和组合框的内部 `QLineEdit` 不再被视为明确文本输入；普通按钮、树视图和滑块操作不会保留输入法。
- iOS 的 `NodeView` 使用 `NoEditTriggers`，普通触摸、双击和焦点变化不会隐式进入图层改名。
- `LayerBox::slotRenameCurrentNode()` 仍可显式调用 `edit()`，其编辑器带明确文本输入标记，因此“重命名图层”动作保留。

涉及文件：

- `upstream/krita/libs/ui/opengl/kis_opengl_canvas2.cpp`
- `upstream/krita/libs/ui/canvas/kis_qpainter_canvas.cpp`
- `upstream/krita/plugins/dockers/layerdocker/NodeView.cpp`
- `upstream/krita/libs/ui/input/kis_input_manager.cpp`

### 3.3 语言资源

2026-09-26 的真机反馈显示下列打包检查不足以确认正文翻译：只有 Qt/KDE 按钮为中文，Krita 正文仍为英语。后续修复将 locale 注册提前到正式应用构造之前，并补齐 KI18n 静态 gettext 缓存探测的链接依赖；诊断与回归详见[正文翻译与简繁切换修复](localization-repair-2026-09-27.md)。

- iOS 的 `krita` target 依赖 `pofiles` 与 `tsfiles`，直接构建应用时会先生成翻译。
- 增加带 `krita` component 的安装规则，将 Krita catalog 和静态 KDE Frameworks catalog 复制到 `krita.app/share/locale`；Xcode Run 的构建后安装也能取得这些资源。
- iOS 启动时显式把 app 内 `share/locale` 注册给 `KLocalizedString`，ECM `.qm` 也直接从 bundle 路径加载。
- Info.plist 声明 `en`、简体中文、繁体中文、日语和韩语本地化。
- 应用门禁要求简繁中文的 `krita.mo` 和 `kconfig6_qt.qm` 存在，缺失会直接失败。

最新 app 中共有 859 个语言文件，约 54,076,760 bytes；已确认以下文件存在：

- `share/locale/zh_CN/LC_MESSAGES/krita.mo`
- `share/locale/zh_TW/LC_MESSAGES/krita.mo`
- `share/locale/zh_CN/LC_MESSAGES/kconfig6_qt.qm`
- `share/locale/zh_TW/LC_MESSAGES/kconfig6_qt.qm`

## 4. 构建与自动验证结果

2026-09-24 已完成：

- `krita` ARM64 iOS device Debug 增量编译：通过。
- 翻译生成：`pofiles` 与 `tsfiles` 均执行。
- 应用架构与平台：ARM64 / iOS device，通过。
- 动态依赖：仅系统库，通过。
- 默认资源包：4 个，通过完整性检查。
- 静态 qrc：14/14，通过。
- 简繁中文 Krita/KF6 catalog：通过新增门禁。
- 未签名 IPA 二次 ZIP/内容检查：通过。
- 完整 Xcode 工程刷新：通过，工程含 Pencil 桥、输入法修改和翻译 targets。
- Xcode `krita` scheme、Debug、generic iOS device：`BUILD SUCCEEDED`。
- Xcode 签名应用门禁：ARM64 / iOS device / signed、仅系统动态依赖、4 个默认 bundle、14 项静态 qrc 和语言 catalog，全部通过。
- Xcode 签名信息：Bundle ID `org.example.krita`、Team ID `<personal-team-id>`、Provisioning Profile `iOS Team Provisioning Profile: org.example.krita`。
- Xcode Release `krita` scheme：`-O3`、`NDEBUG`、`BUILD SUCCEEDED`；应用门禁通过。
- Release 覆盖安装到 11 英寸 iPad Pro M5：通过；21:17:09 启动为 PID 3705，等待 15 秒未产生新 Krita `.ips`。

产物：

- IPA：`.build/Krita-iPadOS-unsigned.ipa`
- IPA：163,312,825 bytes，SHA256 `4ab24601de1996018ead2ae244745c146afc9152011a919b52067ef88727edde`
- Xcode 工程：`.build/krita-ios-xcode/krita.xcodeproj`
- 历史 Debug、Ninja 和安装暂存产物已于 2026-09-25 清理，需要时可由现有工程和脚本重新生成。
- Xcode 构建日志：`logs/krita-xcode-input-language-build.log`
- 启动修复增量构建日志：`logs/krita-xcode-pencil-swizzle-fix-build.log`
- 最新签名 Release App：`.build/krita-ios-xcode/bin/Release/krita.app`，1,466 个文件、259,060,860 bytes；主程序 SHA256 `e9a958e72277b16ca1136efa3e7aba07367d47f318210868493e5a3c507fe837`
- Release 输入/橡皮构建日志：`logs/krita-xcode-release-input-eraser-build.log`
- 源码补丁的 2026-09-24 导出快照（当前文件已更新，见 [2026-09-26 弹窗修复记录](popup-and-picker-repair-2026-09-26.md)）：`patches/ios/krita-ipados.patch`，130,340 bytes，SHA256 `3d0dea2b869f9061959b97fa9ce3a06741e858db919fbcfca902845e67553062`

首次安装后发现 `didMoveToWindow` 的运行时交换误作用于 `UIView` 基类，使 UIKit 键盘内部视图进入 Krita 方法并因未识别 selector 崩溃。修复已先把继承实现复制为 `QUIView` 自己的覆盖，再只交换 `QUIView` 的方法。修复版重新编译、签名并安装后，于 20:59:19 成功启动为 PID 3587；等待 15 秒后未生成新的 Krita `.ips`。`codesign` 可读取嵌入签名、Team ID 与 CodeDirectory；主机严格证书链检查仍返回 `CSSMERR_TP_NOT_TRUSTED`，但实体 iPad 已接受安装并启动。上述结果不代表 Pencil 手势、键盘行为和语言切换已经完成人工验证。

## 5. 实体 iPad 验收顺序

1. 用新构建安装后，手指单击、拖动、双指缩放画布，确认不会打开轮盘。
2. 用 Apple Pencil 笔杆双击，确认当前笔刷直接进入橡皮模式；再次双击恢复原笔刷绘画模式，且工具栏橡皮状态同步。
3. Apple Pencil Pro 捏压一次，确认轮盘在 hover/最近触点附近打开，且不因 changed/ended phase 重复开关。
4. 在绘画过程中触发双击/捏压，确认无误画、无卡死、无新 `.ips`。
5. 选择图层、切换可见性、拖动排序、调整不透明度、点击 Docker 和画布，确认不弹键盘或 Scribble。
6. 使用“重命名图层”，确认编辑框和输入法仍可用；结束改名后键盘能收起。
7. 使用文本工具，确认文本模式可启用输入法，退出文本模式后输入法收起。
8. 将 iPad 或 Krita 语言切到简体中文和繁体中文，完全退出并重启，确认菜单、Docker 与对话框从对应 catalog 加载。

## 6. 完成边界

源码、Release 构建、签名安装和启动已经完成。实体 iPad 通过第 5 节全部项目后，才能把这些输入行为标记为真机完成。当前映射为 Pencil 双击切换橡皮、Pencil Pro 捏压打开轮盘；后续可根据真机体验决定是否尊重系统 preferred action 或提供 Krita 内部开关。
