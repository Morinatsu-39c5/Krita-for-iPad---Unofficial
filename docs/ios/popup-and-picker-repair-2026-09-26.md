# 关闭文档确认框与系统下拉滚轮修复

日期：2026-09-26。源码修改保留在本地，未暂存、未提交。

本文的哈希、大小和 PID 为 2026-09-26 弹窗修复快照。当前签名应用与 IPA 已包含后续正文翻译和简繁切换修复，最新产物与验收见[2026-09-27 语言修复记录](localization-repair-2026-09-27.md)。

## 用户报告

- 关闭文件时，弹出确认窗口有概率失去响应，随后整个应用无法操作。
- 设置中的下拉框可以弹出 Apple 系统滚轮，但无法滚动或选择。

## 代码证据与判断

### 系统滚轮与键盘保护冲突

Qt 6.10.3 的 `QIOSMenu::toggleShowUsingUIPickerView()` 将 `QUIPickerView` 安装为输入对象的 `inputView`，通过 `Qt::ImPlatformData` 查询返回；滚轮同时监听 `UIKeyboardWillHideNotification`，收到通知会取消菜单。现有 Krita 全局保护在非文本触摸后无条件 `QInputMethod::reset()`/`hide()`。Qt 的 reset 会重建输入 responder，hide 会让它 resignFirstResponder。因此，保护软键盘的路径也会撤掉系统选择器。

这确认了代码中的冲突；滚轮失效的完整实机触摸过程还需安装后复测。

参考：[Qt iOS 菜单实现](https://github.com/qt/qtbase/blob/v6.10.3/src/plugins/platforms/ios/qiosmenu.mm)、[Qt iOS 输入法实现](https://github.com/qt/qtbase/blob/v6.10.3/src/plugins/platforms/ios/qiosinputcontext.mm)。

### 同步关闭确认框

`KisView::queryClose()` 原来调用静态 `QMessageBox::warning()`，等待保存使用 `waitForSavingToComplete()`。原生消息框 helper 通过 rootViewController 展示 UIKit alert，并在 `exec()` 中运行嵌套事件循环。当前没有本轮卡住时的线程采样，不能断言每次卡住都由同一条调用链造成；已确认关闭文档仍存在同步弹窗与同步等待的风险。

参考：[Qt iOS 消息框实现](https://github.com/qt/qtbase/blob/v6.10.3/src/plugins/platforms/ios/qiosmessagedialog.mm)。

## 已实施的修改

- 键盘保护先向当前 focusObject 查询 `Qt::ImPlatformData`；发现非空 `inputView` 时保留原生系统选择器。
- 只有输入面板实际可见时才 reset/hide，避免每次点击非文本控件都重建原生 responder。
- 合并重复的延迟隐藏任务，执行时重新检查当前焦点；已经进入显式文本框时不再执行旧的隐藏任务。
- iOS 关闭已修改文档时立即返回 false，下一轮主事件循环显示 Qt Widgets 确认框；确认框设置 `DontUseNativeDialog`，不进入同步 `exec()`。
- 对同一视图的重复关闭请求只保留一个确认流程。
- “取消”保留文档与修改；“不保存”请求取消笔画，定时等待图像空闲与 autosave 结束后，再移除 autosave 并关闭视图。
- “保存”先请求结束笔画，通过 100 ms 定时器等待图像空闲后发起原有保存流程，再检查后台保存是否完成；保存失败、取消或保存期间继续修改时保留文档。等待笔画时不进入同步进度窗口。
- 视图销毁时关闭仍然存在的确认框；定时器和延迟任务以视图为 context，由 Qt 自动取消。
- 非 iOS 平台保留原关闭路径。

涉及源码：`libs/ui/KisView.cpp`、`libs/ui/KisView.h`、`libs/ui/input/kis_input_manager.cpp`。

## 自动回归

运行 `python3 packaging/ios/test-popup-regressions.py`，从当前源码提取本轮生产回调，使用 macOS Qt 6.10.3 Widgets 执行。原生 responder 与文档保存使用确定性的替身；事件过滤器、焦点、消息框和定时器使用真实 Qt。此测试不替代 UIKit 触摸验收。

通过项目：

1. 原生 picker 的 inputView 不被 reset/hide。
2. 普通非文本输入面板仍可隐藏；已隐藏面板不重复 reset。
3. 延迟任务执行前焦点转到文本编辑器时，保留输入。
4. 多次非文本事件合并为一个隐藏任务。
5. 关闭确认异步出现，重复请求不重复弹出。
6. 取消、不保存、保存成功的文档状态和关闭次数。
7. 保存启动失败、后台失败、保存期间新增修改均保留文档。
8. 已有保存结束但文档仍修改时重新确认。
9. 图像仍在运算时，“不保存”和“保存”均异步等待；空闲后继续完成操作。
10. 视图在弹窗前或弹窗后销毁时，不残留模态窗口。

结果：PASS。日志：`logs/krita-popup-regression-2026-09-26.log`。

## 构建与实机验收

已完成：

- Xcode `krita` / Release / ARM64 iOS device 构建：`BUILD SUCCEEDED`，包含最后的异步笔画等待修改；主程序使用 `-O3`、`NDEBUG`。
- 应用门禁：ARM64 / iOS device / signed、仅系统动态依赖、4 个默认 bundle、14 项静态 qrc、简繁中文语言文件，全部通过。
- 签名：Bundle ID `org.example.krita`，Team ID `<personal-team-id>`。
- 覆盖安装到 11 英寸 iPad Pro M5：成功。
- 启动：成功，PID `6648`；23:42:58 的查询确认进程仍在运行。
- 23:43:03 查询近期 Krita 崩溃报告列表：2026-09-25/26 匹配结果为 0 files。此前读取故障报告曾遇到 CoreDevice 连接重置，故关闭卡住问题没有获得本轮现场线程采样。
- IPA ZIP CRC、plist、执行权限和逐文件内容一致性：通过。
- 补丁反向应用检查与 `git diff --check`：通过；没有暂存或提交。

产物：

| 文件 | 结果 |
|---|---|
| `.build/krita-ios-xcode/bin/Release/krita.app` | 1,466 个文件，259,078,924 bytes；主程序 SHA256 `3e1ebfd81498862dfa856cd2aa79f572979d656e435ed2a968b67ecba1d93441` |
| `.build/Krita-iPadOS-Release-signed.ipa` | 118,795,889 bytes；SHA256 `9712a086f57a785c0973995c705cb72362d9a8eeb42ee509a272ff98eaac789c` |
| `patches/ios/krita-ipados.patch` | 139,046 bytes；SHA256 `1ad0a51dd856c8f6e813910fe47404f1669cb08baee1a1af3304b53b0989ac24` |
| `logs/krita-xcode-popup-fix-2026-09-26-final-build.log` | 最终成功构建日志 |
| `logs/krita-popup-app-validation-2026-09-26.log` | 应用完整性检查 |
| `logs/krita-popup-install-2026-09-26.json`、`logs/krita-popup-launch-2026-09-26.json` | 实机安装、启动成功记录 |

历史 `.build/Krita-iPadOS-unsigned.ipa` 仍是 2026-09-24 的 Debug 包，不包含本轮修复。启动成功和宿主自动回归不等同于弹窗触摸功能已完成实机验收。

实机验收顺序：

1. 修改文档后关闭，连续测试“取消”“不保存”“保存”；检查回到画布或欢迎页后菜单和画布仍能操作。
2. 连续多次打开/取消关闭确认，包含快速重复关闭动作。
3. 保存时保持文档开启，确认保存结束后才关闭；保存失败时文档保留。
4. 设置中打开下拉框，滚动系统滚轮并点击 Done，检查实际值更新；再次打开并 Cancel，检查值未变化。
5. 下拉框结束后测试普通图层操作不误弹键盘，同时显式改名仍能输入。

批量关闭/会话退出中的同步 bool 调用者仍会在首个异步确认时返回 false；当前异步完成后关闭的是所确认的文档视图。批量操作的连续恢复属于后续验收范围。
