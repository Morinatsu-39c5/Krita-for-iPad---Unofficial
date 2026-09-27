# Krita iPadOS 修复进度

更新日期：2026-09-24  
依据：[独立评审](project-review-2026-09-23.md)与[修复计划](repair-plan-2026-09-23.md)。  
代码状态：修改保留在本地，未暂存、未提交。

## 1. 本轮结论

启动失败的构建级根因已修复：Krita iOS 主程序现在会显式初始化静态归档中的 14 组 qrc 资源，并在资源数据库启动前检查每组资源的哨兵路径。最初缺失的 `:/create_version_information.sql` 已包含在这套通用机制中。

Debug Ninja 与 Xcode 两条构建链都已完成 ARM64 device 构建。完整 Xcode 工程现已可生成、可编译，且直接构建的 `.app` 会自动包含 Krita 的运行时 `share` 资源树。Xcode 工程也已用开发团队签名完成全量构建，并在实体 iPad 上安装、启动成功。

启动问题已经完成真机闭环：用户确认 SQL、数据库和默认 bundle 错误消失，主窗口出现且第二次启动正常。随后出现的“新建文件会闪退”先由 UIKit run-loop 报告定位为约 0.55 秒的主线程同步初始化卡顿；分阶段后又通过设备 `.ips` 定位并修复颜色三角形顶点 NaN 和颜色历史空文档两处崩溃。进入画布后的另两次 `EXC_BAD_ACCESS` 已定位到 Qt iOS 保存的 Pencil `UITouch` 悬空指针并加入保护。保护版完成 180 秒高频 Pencil 实机测试；UIKit 在测试中实际报告了部分触控取消，应用仍未崩溃，也没有生成新的系统报告。

## 2. 已完成修复

### 2.1 静态 qrc 资源

- 在各资源所属 CMake target 旁登记资源名、哨兵路径和 qrc 源文件。
- 由 CMake 生成 `krita_ios_resources.cpp`，在 `main()` 最早阶段调用全部资源初始化函数。
- 启动前通过 `QResource` 检查 14 个哨兵；缺失时明确记录错误并停止，避免进入数据库后的连锁报错。
- 将 basic tools 的资源初始化名改为 `basictools`，保留 flake/default tool 的 `defaulttools`，消除静态链接时的同名符号风险。
- 最终验证清单包含：`sql`、`kxmlgui`、`kisquickwidgets`、`textproperties`、`pathshapes`、`basictools`、`defaulttools`、`selectiontools`、`toolcrop`、`tool_polygon`、`polyline`、`tool_transform`、`karbontools`、`svgtexttool`。

### 2.2 应用与 IPA 门禁

- 应用检查器不再使用可被 `python3 -O` 移除的 `assert`。
- 检查 ARM64、iOS device 平台、plist、签名状态、系统动态依赖、默认 bundle、无 `.a`、无符号链接和 14 组 qrc 初始化符号。
- IPA 通过临时文件生成，重新打开检查 ZIP CRC、路径集合、文件内容与权限后再原子替换正式文件。
- 故障注入验证了优化模式与缺失 qrc 时会非零退出。

### 2.3 补丁保护

- 补丁导出会验证 Krita checkout 与固定 HEAD。
- 默认拒绝空补丁，包含已跟踪和未跟踪文件，并在替换正式文件前执行反向应用检查。
- 输出通过临时文件、`fsync` 和原子替换更新，失败不会覆盖已有补丁。

### 2.4 完整 Xcode 工程

- iOS/Xcode 的 Qt 补丁探测改为只编译检查，不把 Qt 静态资源对象 target 传播到 `try_compile` 子工程。
- Qt 私有头文件使用可在子工程中解析的实体 include 路径。
- `configure-krita-xcode.sh --fresh` 已成功生成完整工程。
- 主 `krita` scheme 已用 `CODE_SIGNING_ALLOWED=NO` 完整构建成功。
- Xcode 主 target 的构建后阶段会安装 `krita` 数据组件并复制 `share` 树；`kritalibkis` 与 `kritaexifcommon` 被列为显式依赖，保证安装组件完整。
- `configure-krita-xcode.sh` 默认保持未签名；显式提供 `KRITA_IOS_TEAM_ID` 时会允许 Xcode 使用该团队签名。
- 签名只对最终 `krita` 应用 target 启用；静态库和插件 target 保持 `CODE_SIGNING_ALLOWED=NO`，消除了数百个中间 target 的 Team ID 报错。
- `run-krita-device.sh` 会增量刷新工程，再使用 target 级签名配置进行构建、安装和启动，不向所有 target 注入全局签名参数。

## 3. 已验证产物

### 3.1 正式 Ninja 产物

- 应用：`.build/krita-ios-install/krita.app`
- IPA：`.build/Krita-iPadOS-unsigned.ipa`
- IPA 大小：163,312,825 bytes
- IPA SHA256：`4ab24601de1996018ead2ae244745c146afc9152011a919b52067ef88727edde`
- 2026-09-24 导出快照的补丁 SHA256（当前文件已更新，见 [2026-09-26 弹窗修复记录](popup-and-picker-repair-2026-09-26.md)）：`3d0dea2b869f9061959b97fa9ce3a06741e858db919fbcfca902845e67553062`
- 应用验证：Debug、ARM64 iOS device、未签名、仅系统动态依赖、4 个默认 bundle、14 组必需 qrc 资源，以及简繁中文 Krita/KF6 catalog，全部通过。
- 应用文件：1,461 个、510,195,328 bytes；其中语言资源 859 个、54,076,760 bytes。

### 3.2 Xcode 产物

- 工程：`.build/krita-ios-xcode/krita.xcodeproj`
- scheme：`krita`
- 已签名应用：`.build/krita-ios-xcode/bin/Debug/krita.app`
- 已签名 Release 应用：`.build/krita-ios-xcode/bin/Release/krita.app`
- 最新已签名 Debug 应用文件数/大小：1,466 / 492,948,588 bytes；语言文件：859 / 54,076,760 bytes。
- 签名标识：Bundle ID `org.example.krita`，Team ID `<personal-team-id>`。
- 构建验证：完整 `krita` scheme、Debug、ARM64 iOS device 构建成功；此前报错的静态插件均在不签名状态下完成构建。
- 真机验证：设备 `00008142-000918E13440C01C` 接受安装，`devicectl` 使用 Bundle ID 成功启动应用。
- 最终增量复跑通过 `codesign --verify --deep --strict`；证书链、Bundle ID 和 Team ID 均可读取。实体设备安装和启动也已通过。
- Release 应用已按 `-O3` 与 `NDEBUG` 构建；相同应用门禁、签名、安装和启动均通过，触控保护符号已在最终二进制中确认。用户完成画布测试后确认卡顿和偶发闪退看起来已经解决。
- 加入 Pencil、输入法和语言修改后，完整 Xcode Debug `krita` scheme 已再次构建成功；Provisioning Profile 为 `iOS Team Provisioning Profile: org.example.krita`，签名应用门禁通过。主机严格证书链检查当前返回 `CSSMERR_TP_NOT_TRUSTED`，实体 iPad 已接受签名应用安装与启动。

对应日志：

- `logs/krita-final-configure.log`
- `logs/krita-app-build.log`
- `logs/krita-app-validation.txt`
- `logs/krita-ipa-validation.txt`
- `logs/krita-xcode-configure-fixed2.log`
- `logs/krita-xcode-build.log`
- `logs/krita-xcode-build-runtime-data3.log`
- `logs/krita-xcode-app-validation.txt`
- `logs/krita-xcode-signed-device.log`
- `logs/krita-xcode-signed-app-validation.txt`
- `logs/krita-xcode-input-language-build.log`
- `logs/krita-xcode-pencil-swizzle-fix-build.log`
- `logs/krita-xcode-release-input-eraser-build.log`

## 4. 新建文档退出修复

- `.ips` 为 UIKit run-loop 卡顿报告：548 ms、55 个采样，主线程约 515 ms CPU，随后 `SIGABRT`。
- 符号化调用链落在新建对话框的 `documentSelected` → `startCustomDocument` → `addViewAndNotifyLoadingCompleted` 同步路径。
- 内存和 GPU 证据均不支持 OOM 或 OpenGL 初始化故障。
- iOS 路径现把欢迎页切换、视图创建、视图挂载拆到三个事件循环阶段；非 iOS 路径不变。
- 新方法、三个定时回调和调用点已在最终 ARM64 二进制符号表中确认。
- 分阶段后的 `krita-2026-09-24-134357.ips` 与 `134814.ips` 定位到颜色三角形顶点 `0 / 0` 产生 NaN；现已检查有限值、避免零除并限制 HSV 范围。
- 随后的 `krita-2026-09-24-135548.ips` 定位到颜色历史 Docker 在 ViewManager 当前文档尚为空时解引用；现改为从画布自己的 `KisView` 取文档并保护可空连接。
- 修复后的签名应用已在实体 iPad 上运行观察 180 秒，越过上述调用点，退出码为 0；随后查询同一时段的设备崩溃目录为 `0 files`。
- 详细证据见[新建文档卡顿记录](new-document-runloop-hang-2026-09-24.md)。

### 4.1 画布 Pencil 触控闪退

- `krita-2026-09-24-140712.ips` 与 `140744.ips` 都是主线程 `EXC_BAD_ACCESS`，调用链为 `objc_msgSend` → `-[__NSSetM containsObject:]` → `-[QUIView handleTouches:...]`。
- 本地 Qt 6.10.3 平台插件的崩溃地址对应 `quiview.mm` 第 414 行；`m_activePencilTouch` 是未 retain 的原始 `UITouch *`。
- 新增 iOS 专用运行时保护，在 Qt 处理期间强持有 Pencil touch，并在下一次触控开始前清除异常 UIKit 取消序列留下的过期状态。
- 保护版签名 Debug 应用完成 180 秒快速绘画、反复抬笔及手指手势混合测试。控制台实际出现 `Subset of active touches cancelled by UIKit`，应用仍保持运行，测试后没有新增 `.ips`。
- `141142.ips` 与 `141346.ips` 位于应用终止时的嵌套模态对话框，不属于同一画布自然崩溃。
- 详细证据见[画布触控闪退与卡顿记录](canvas-touch-crash-and-performance-2026-09-24.md)。

### 4.2 Pencil 橡皮/轮盘、输入法与语言

- `UIPencilInteraction` 已安装到 Qt 的 iOS 视图；Pencil 笔杆双击触发 `erase_action` 在当前笔刷和橡皮模式之间切换，Pencil Pro 捏压进入现有轮盘且只响应 began phase。
- iOS 输入配置已跳过 `Show Popup Widget` 的触摸快捷键，手指不再由该单指绑定打开轮盘。
- 两种画布在 iOS 默认关闭输入法，文本工具进入文本模式时动态开启；退出时 reset 并隐藏输入面板。新增全局焦点/触摸守卫，在非文本操作后再次隐藏输入法，并排除数值微调框和组合框的内部编辑器。
- iOS 图层树禁止默认编辑触发器，显式“重命名图层”动作仍可创建编辑器。
- `krita` target 现在生成并安装 Krita catalog，同时把静态 KDE Frameworks catalog 打进 app；最新应用含 859 个语言文件。
- ARM64 Debug 编译、应用门禁、IPA 二次检查及完整 Xcode 签名 Debug 构建均通过。上述行为尚未在实体 iPad 上验证。
- 首次安装暴露出 `didMoveToWindow` 交换到了 `UIView` 基类的问题，UIKit 键盘内部视图因此进入 Krita 方法并产生未识别 selector 异常。现先在 `QUIView` 上实体化继承方法，再只交换该子类方法。
- 修复版重新编译、签名、覆盖安装并于 20:59:19 启动成功；设备返回 PID 3587，等待 15 秒未产生晚于 20:56:03 的新 Krita 崩溃报告。
- 用户报告该 Debug 版画布再次卡顿且键盘仍会弹出；最新修改改用 `-O3`/`NDEBUG` Release 构建，21:17:09 覆盖安装并启动为 PID 3705，等待 15 秒未产生新 Krita `.ips`。
- 详细实现与验收矩阵见[Pencil 轮盘手势、输入法与语言修复记录](input-gesture-and-keyboard-plan-2026-09-24.md)。

## 5. 下一步真机验收

已签名的 Xcode Release 应用已安装并完成画布测试；以下基础步骤已由本轮测试覆盖，后续回归继续沿用：

1. 启动并进入已经通过的 Krita 主窗口。
2. 点击“新建文件”，采用默认尺寸并确认。
3. 对话框关闭，画布和工具界面可见。
4. 普通画笔能留下笔迹，再连续新建第二个文档。
5. 快速连续使用 Pencil、抬笔重落并混合手指平移/缩放，比较 Release 与此前 Debug 的跟手性。

保存流程已改为直接写入“在我的 iPad 上/Krita”对应的应用 `Documents`，并绕过 iOS 上无响应的同步文件对话框。下一次真机测试应保存新画布、在“文件”App 中确认 `.kra`、关闭后重新打开并检查图层和笔迹。详见[沙盒保存记录](files-save-sandbox-2026-09-24.md)。Debug 产物只用于功能闭环，不用于性能结论。触控根因和验证证据见[画布触控闪退与卡顿记录](canvas-touch-crash-and-performance-2026-09-24.md)。

最新源码的 Xcode 签名 Release 应用已安装并启动。现在需要人工验证：画布恢复流畅、手指不打开轮盘、Pencil 双击在当前笔刷/橡皮间切换、Pencil Pro 捏压只打开一次轮盘、图层和 Docker 普通操作不弹键盘、显式改名与文本工具仍能输入，以及简体/繁体中文切换后重启生效。

## 6. 尚未完成

- Release 长时间绘画、大画布和复杂笔刷的持续稳定性。
- 连续第二次新建的专项回归。
- 完整应用中的 Pencil 压力/倾斜、手指手势分离、图层撤销、`.kra` 保存重开的真机验证。
- iCloud Drive/第三方文件提供商的异步导出、150% 可配置 GUI 缩放和 `.kpp`/`.bundle`/`.abr` 导入。
- Pencil 笔杆双击橡皮切换、Pencil Pro 捏压轮盘、单指解绑、全局输入法守卫与图层编辑边界的实体 iPad 验收。
- 简体/繁体中文系统或应用语言切换、重启和主要界面翻译的实体 iPad 验收。
- 修复计划中依赖 pin、下载完整性、依赖清单和新环境复现性等后续项目。

输入与语言问题的原因、实现、构建证据和真机验收标准见[Pencil 轮盘手势、输入法与语言修复记录](input-gesture-and-keyboard-plan-2026-09-24.md)。
