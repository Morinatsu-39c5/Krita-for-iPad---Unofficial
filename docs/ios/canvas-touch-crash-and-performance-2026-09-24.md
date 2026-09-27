# Krita iPadOS 画布触控闪退与卡顿记录

更新日期：2026-09-24  
代码状态：修复保留在本地，未暂存、未提交。

## 1. 问题结论

用户进入画布并绘画后观察到卡顿和偶发闪退。设备报告证明，闪退的直接原因是 Qt 6.10.3 iOS 平台插件保存了一个不持有所有权的 Apple Pencil `UITouch` 指针。UIKit 在异常触控序列中可能只取消部分触控，导致 Qt 保存的指针在下一次 `touchesBegan:` 或 `touchesEnded:` 中已经失效；Qt 随后把该指针传给 `NSSet containsObject:`，最终在 `objc_msgSend` 中发生 `EXC_BAD_ACCESS`。

卡顿与闪退不是同一个故障。此前实机使用的 Debug 应用按 `-O0` 编译，而且画布操作期间会连续输出大量诊断信息，因此不能用它判断最终绘画性能。触控闪退修复先在 Debug 构建中完成压力测试，随后又以独立 Release 优化版完成真机验证。

## 2. 崩溃证据

以下两份报告是画布触控的真实崩溃：

- `logs/device-crashes/krita-2026-09-24-140712.ips`
- `logs/device-crashes/krita-2026-09-24-140744.ips`

两份报告的共同特征：

- 异常：`EXC_BAD_ACCESS` / `SIGSEGV`
- 线程：主线程
- 顶部调用：`objc_msgSend` → `-[__NSSetM containsObject:]`
- Qt 调用：`-[QUIView handleTouches:withEvent:withState:withTimestamp:]`
- 入口分别落在 `touchesBegan:withEvent:` 或 `touchesEnded:withEvent:`

另外两份报告不是画布自然运行时的同类闪退：

- `krita-2026-09-24-141142.ips`：应用终止时停在 `KisView::queryClose()` 的嵌套对话框。
- `krita-2026-09-24-141346.ips`：应用终止时停在语言设置对话框。

这两份报告都经过 Qt 的 `applicationWillTerminate`/终止路径，和当时的重新安装或外部终止一致，不能当作 Pencil 绘画崩溃。

## 3. 精确根因

本地 Qt iOS 静态平台插件位于：

`/.qt/6.10.3/ios/plugins/platforms/libqios_debug.a`

对 `quiview.mm.o` 反汇编并和 Qt 6.10.3 源码对应后，崩溃偏移落在 `src/plugins/platforms/ios/quiview.mm` 第 414 行附近：

```objective-c++
if (m_activePencilTouch && [touches containsObject:m_activePencilTouch])
```

`m_activePencilTouch` 的类型是原始 `UITouch *`，赋值时没有 retain。实机控制台在压力测试中出现了 `Subset of active touches cancelled by UIKit`，说明 UIKit 确实会产生不完整的结束/取消序列。旧代码在这种序列之后可能保留悬空指针，下一次集合比较就会向已释放对象发送 Objective-C 消息。

Qt 开发分支当前仍使用同样的原始指针写法，因此仅切换一个 Qt 小版本不能作为已经验证的修复。

## 4. 本地修复

新增 `upstream/krita/krita/krita_ios_touch_guard.mm`，并在 iOS 的 `main()` 最早阶段安装保护。保护通过 Objective-C runtime 包装 `QUIView` 的三个入口：

- `touchesBegan:withEvent:`
- `touchesEnded:withEvent:`
- `touchesCancelled:withEvent:`

处理规则：

1. 将活跃的 Pencil `UITouch` 保存在与 `QUIView` 关联的强引用集合中，保证 Qt 处理期间对象仍然存活。
2. 新触控序列开始前，检查 Qt 的 `m_activePencilTouch`。如果它不属于本次触控集合，先清空这个过期状态，再进入 Qt 原实现。
3. 结束与取消回调在 Qt 完成 `handleTouches()` 后再释放保护引用。

这一修复只在 iOS 构建中加入，不改变桌面和 Android 路径。它依赖 Qt 6.10 当前的 `QUIView` 类名和 `m_activePencilTouch` ivar 名，升级 Qt 后必须重新核对。

## 5. 已完成验证

Debug 签名应用重新构建、安装并启动成功。随后进行了 180 秒实机 Pencil 压力测试，包括快速连续绘画、抬笔重落和手指平移/缩放。

测试结果：

- UIKit 实际报告过 `Subset of active touches cancelled by UIKit`。
- 应用在完整观察窗口中保持运行，进程退出码为 0。
- 测试后查询同一时段的设备诊断目录，没有新增 Krita `.ips`。

这证明修复至少覆盖了本次两份报告所显示的失效指针路径。更长时间绘画、后台恢复、Pencil 压力/倾斜和多指手势仍需继续验收。

## 6. 性能判断与下一步

Debug 运行记录显示：

- 应用按 `-O0` 编译。
- 画布期间反复输出无法读取 RAM 大小、排序区域设置、事件循环及 OpenGL/后台状态等诊断信息。
- 控制台附加本身也会增加运行开销。

因此 Debug 卡顿不能直接归因于画布算法。本轮生成的 Release 应用明确使用 `-O3` 与 `NDEBUG`，并通过签名、资源和动态依赖门禁后安装到实体 iPad。用户在不附加实时控制台的情况下测试画布，确认卡顿与偶发闪退看起来已经解决。若后续在大画布或复杂笔刷下再次出现卡顿，再使用 Instruments 分别采集主线程、渲染和内存数据。

## 7. 当前验收边界

- 已确认：触控崩溃调用链、Qt 悬空指针根因、保护代码编译与签名、180 秒压力测试无新崩溃、Release 真机安装与用户画布测试通过。
- 待确认：长时间绘画、大画布与复杂笔刷稳定性。Release 测试后的系统报告查询受到 Xcode CoreDevice 服务超时影响，因此本轮 Release 结论以用户未观察到闪退为依据；此前 Debug 压力测试已有“无新增 `.ips`”证据。
- 尚未宣称：压感、倾斜、复杂笔刷、大画布、多图层和后台恢复已经通过。
