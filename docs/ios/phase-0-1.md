# 阶段 0–1 实测报告

日期：2026-09-22。范围：环境确认 + 独立 Qt Widgets 验证程序。未进入完整 Krita 的阶段 2。

## 环境

| 项目 | 实测结果 |
| --- | --- |
| macOS | 15.7.8 / 24G812 |
| CPU | arm64 |
| Xcode | 26.3 / 17C529 |
| Developer directory | /Applications/Xcode.app/Contents/Developer |
| iOS SDK | 26.2 |
| CMake | 4.4.3 |
| Qt | 初始未找到 kit；本轮安装官方 6.10.3 iOS + macOS qtbase |
| 设备 | devicectl 检测到 available (paired) 的 iPad Pro 11-inch (M5), iPad17,1 |
| 生成 iPadOS 二进制 | 可以，已实际成功 |
| 签名 | 未签名；本轮用户选择先交付未签名版本 |

## 实际结果

- CMake Xcode 工程生成成功。
- Xcode `** BUILD SUCCEEDED **`：包含 Objective-C++ Files 导出桥接和图标。
- `file`：Mach-O 64-bit executable arm64。
- `vtool -show-build`：platform IOS、minos 17.0、sdk 26.2。
- Qt iOS 静态平台和图像格式插件完成链接；不存在运行时安装外部二进制插件的实现。
- macOS 同源探针编译通过；offscreen 自动测试通过五档 UI 比例、固定图像尺寸、平移坐标转换、模拟 tablet 事件路径及拒绝合成鼠标落笔。
- Info.plist 与脚本语法检查通过。

自动化测试使用模拟 Qt 事件，不能证明 Apple Pencil 真机输入正常。iPad 安装、运行、菜单显示、控件可点击性、安全区域、原生 Files、GL 可见输出、真实压感/倾斜均为 **未验证**。

## 本轮支持范围

探针包含 QMainWindow、菜单、工具栏、Dock、非阻塞对话框；150% 默认、100/125/150/175/200% 可持久化配置；字体及图标、按钮、滚动条等选定样式指标缩放。图片固定 1024×768、DPR=1；显示 DPR 由 Qt 管理，未设置 QT_SCALE_FACTOR。

使用 QTabletEvent 显示位置、压力、倾斜和事件计数，压力决定线宽；触摸只平移、不画线，拒绝合成鼠标绘制，真实鼠标可以绘制。键盘可测试 Open / Save As / Clear / Reset view。栅格画布可绘制，另有可按需创建的 QOpenGLWidget 持续刷新测试。

导入使用 Qt 原生 ExistingFile 选择器；Qt 6.10.3 的平台代码调用 `initForOpeningContentTypes:asCopy:YES`。探针再复制到 AppData/imports 下的唯一文件名，避免依赖外部文件长期访问权限。普通资源只按数据复制，不执行、不注册为插件。

Qt 6.10.3 `QIOSFileDialog::show` 对 AcceptSave 返回 false，所以 iOS PNG 导出增加 FilesExport.mm，使用 `initForExportingURLs:asCopy:YES`。导出暂存文件的生命周期由完成/取消回调持有；选择器 delegate 在呈现期间被保留。原生流程是否对指定 iCloud/provider 正常工作仍须真机确认。

## 真实错误与处理

首次沙盒内配置失败：`No CMAKE_CXX_COMPILER could be found`，来源为 `project()` 的 Xcode compiler-identification 步骤。日志同时记录 Xcode 缓存/服务访问问题。允许在正常主机开发环境重试后，AppleClang 17.0.0.17000604 探测成功，原配置错误已消除。新增 Objective-C++ 探测同样需要正常 Xcode 权限。

未签名构建当前无阻塞错误。下一道阶段门槛是签名并完成设备验收；按用户要求未继续请求签名权限或尝试安装未签名应用。

## 已知限制和下一步

1. 阶段 1 尚未通过完整真机验收；不能标记“已在 iPad 上绘画”。
2. 这是平台探针，未包含 Krita 图层、撤销、.kra、PSD、笔刷引擎、资源数据库、自动保存或崩溃恢复。
3. 资源文件仅复制，PNG 仅导出；尚无完整文档打开和另存为语义。原文件不被覆盖。
4. 缩放仅是独立探针验证方案，尚未泛化 KisAndroidScaling；原 Krita 源码未被修改。不能据此宣称 Krita 画布不存在双重缩放。
5. 为阶段 1 固定横屏并避免 Xcode 方向校验警告，设置 UIRequiresFullScreen；Split View/Stage Manager 与新系统窗口策略尚未验证，后续应恢复并测试可用窗口模式。
6. UIKit 仅用于系统导出选择器；未改写前端。尚未证明有必要增加 Pencil 输入桥接。
7. QOpenGLWidget 已可编译链接；这不是实际 OpenGL 渲染成功的证据，未启动专用 Metal 移植。
8. 本轮未禁用或删除任何 Krita 功能；未来候选禁用项及影响列于 dependencies.md，不能当成已实施。

## 最终交付状态

按用户后续要求：**不提交 Git**。所有文件保留在工作目录中，未创建 commit；完整 Krita checkout 无修改。
最终应用含 Assets.car 和 iPad 图标，Info.plist 设备族为 iPad，二进制再次核验为 ARM64/iOS 17.0。

工程：`.build/ios-probe/KritaIOSProbe.xcodeproj`。应用：`.build/ios-probe/Debug-iphoneos/KritaIOSProbe.app`。

## 用户真机反馈（2026-09-22 后续）

用户反馈“实机ok”，批准进入阶段2。提供的截图显示真机运行 Widgets Probe、150% GUI、粗细变化的笔迹和手指仅平移事件。将启动/GUI/基础绘画记为用户确认；没有据截图单独推断 OpenGL、iCloud、倾斜完整测试结果。
