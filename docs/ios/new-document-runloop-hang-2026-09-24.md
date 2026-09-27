# Krita iPadOS 新建文档卡顿退出记录

日期：2026-09-24  
状态：已完成原始卡顿与两处后续崩溃的定位和修复；签名 Debug 应用已完成 3 分钟实机运行观察，新建路径越过已知崩溃点且没有生成新 `.ips`。  
代码状态：修改保留在本地，未暂存、未提交。

## 1. 用户确认的前置结果

用户已在实体 iPad 上确认上一轮启动修复的第 1–4 项通过：SQL 资源错误消失、资源数据库与默认 bundle 错误消失、Krita 主窗口出现、再次启动仍可进入主窗口。随后发现“新建文件会闪退”。这说明启动资源问题已经越过真机门槛，当前阻塞转移到首次创建画布。

## 2. 报告与结论

分析对象：`UIKit-runloop-krita-2026-09-24-112940 2.ips`  
报告 SHA256：`be015733c1f338b4233323c760e7330df44f659290e9f4028bfa3576cc309c20`

该文件是 `bug_type 328` 的 UIKit run-loop 卡顿报告，不是常规未捕获异常报告。关键证据如下：

- 事件为 `Completed Runloop Hang`，持续约 548 ms，共 55 个约 10 ms 的采样。
- 主线程在约 548 ms 内消耗约 515 ms CPU，随后记录 `exitedAfterHang` 和 `SIGABRT`。
- 应用内存约 395 MB，系统仍有约 4.4 GB 可用内存，不支持内存耗尽判断。
- OpenGL/Metal 初始化只占极少采样，不支持将故障归因于 GPU 初始化。
- 报告设备为 `iPad17,1`，系统为 iPadOS 27.0（24A437）。

因此，现有证据支持“新建文档按钮事件中的同步主线程工作触发 UIKit 卡顿终止”，不支持普通 C++ 异常、内存耗尽或 OpenGL 初始化失败。

## 3. 符号化结果

报告没有列出 Krita 主二进制 UUID，但本地对应 IPA 的可执行文件保留了符号。以 `qt_main_wrapper` 的本地与运行时地址计算 ASLR 基址 `0x100758000` 后，`atos` 可以稳定还原调用链。

主要调用路径为：

```text
KisWelcomePageWidget::slotNewFileClicked
  -> KisMainWindow::slotFileNew
  -> QDialog::exec
  -> KisCustomImageWidget::createImage
  -> KisOpenPane::documentSelected
  -> KisPart::startCustomDocument
  -> KisMainWindow::addViewAndNotifyLoadingCompleted
  -> showWelcomeScreen(false)
  -> KisPart::createView
  -> KisMainWindow::addView
  -> KisView::setViewManager
  -> KoToolManager::attachCanvas / createCanvasData
```

54 个主线程样本位于“新建”对话框的嵌套事件循环内，其中 53 个样本从 `KisCustomImageWidget::createImage()` 进入 `KisPart::startCustomDocument()`。较重的两段分别是主窗口/欢迎页布局恢复，以及视图、工具选项、工具和画布挂载。

原路径在发出 `documentSelected(doc)` 后同步完成全部视图初始化，直到返回后才调用对话框的 `accept()`。这使按钮事件连续占用主线程约 0.55 秒，正好覆盖报告中的卡顿时间窗。

## 4. 第一阶段修复：拆分主线程初始化

修复限定在 `Q_OS_IOS`：

1. `KisPart::startCustomDocument()` 仍立即把文档加入 Krita 文档列表，保证所有权稳定。
2. 使用以主窗口为 context 的零延时 `QTimer`，让新建对话框先退出当前按钮事件。
3. 将欢迎页切换、`KisView` 创建、视图挂载与完成通知拆到三个连续的主线程事件。
4. 每一阶段都用 `QPointer` 检查文档和视图生命周期；主窗口销毁时 Qt 会取消以其为 context 的回调。
5. 非 iOS 平台继续使用原同步函数，其他打开文档和创建视图的调用点不变。

改动文件：

- `upstream/krita/libs/ui/KisPart.cpp`
- `upstream/krita/libs/ui/KisMainWindow.h`
- `upstream/krita/libs/ui/KisMainWindow.cpp`

## 5. 分阶段后暴露的两处崩溃

分阶段修复让程序越过原来的 UIKit HangTracer 门槛，也使两个原本被遮蔽的普通崩溃能够被设备报告准确定位。设备报告已复制到 `logs/device-crashes/`。

### 5.1 高级颜色选择器顶点产生 NaN

报告 `krita-2026-09-24-134357.ips` 和 `krita-2026-09-24-134814.ips` 的主线程调用链为：

```text
qRound(float)
  -> QColor::fromHsvF
  -> KisDisplayColorConverter::fromHsvF
  -> KisColorSelectorTriangle::colorAt
  -> Acs::PixelCacheRenderer::render
```

三角形顶点处的水平线长度为零，旧实现计算 `relativeX / horizontalLineLength`，得到 `0 / 0` 的 NaN；Qt 6.10 Debug 的数值检查随后终止进程。`KisColorSelectorTriangle::colorAt()` 现使用浮点几何，检查非有限输入和无效高度，在顶点使用零饱和度，并将 HSV 分量限制到有效范围。

改动文件：`upstream/krita/plugins/dockers/advancedcolorselector/kis_color_selector_triangle.cpp`。

### 5.2 颜色历史使用尚未成为当前文档的画布

数值修复后的报告 `krita-2026-09-24-135548.ips` 显示：

```text
KisDocument::colorHistoryModel()
  -> KisColorHistory::setCanvas(KisCanvas2*)
  -> KisColorSelectorNgDockerWidget::setCanvas
  -> KoCanvasControllerWidget::Private::activate()
```

分阶段挂载画布时，Docker 已收到新画布，但 `canvas->viewManager()->document()` 仍可能暂时为空。旧代码随即无条件调用该空文档的 `colorHistoryModel()`。修复改为从画布自己的 `KisView` 取得 `resourceProvider()` 和 `document()`，并只在对象存在时连接信号；颜色历史模型原有的 fallback 继续处理短暂缺失状态。

改动文件：`upstream/krita/plugins/dockers/advancedcolorselector/kis_color_history.cpp`。

`krita-2026-09-24-135106.ips` 位于文件打开流程，并发生在应用被要求终止期间，不是“新建文档”故障。`krita-2026-09-24-134425.ips` 是另一条 Qt iOS 触摸处理 `EXC_BAD_ACCESS`，也不属于本次新建路径；两者保留用于后续专项处理。

## 6. 构建与静态验证

- `git diff --check`：通过。
- Debug ARM64 iOS device 增量编译与链接：通过。
- 成品符号表包含 `KisMainWindow::addViewAndNotifyLoadingCompletedStaged(KisDocument*)` 及三层 `QTimer::singleShot` 回调。
- 应用门禁：ARM64、iOS device、未签名、仅系统动态依赖、4 个默认 bundle、14 组静态 qrc，全部通过。
- IPA ZIP CRC、逐文件内容、权限和 plist 检查：通过。
- 新 IPA：`.build/Krita-iPadOS-unsigned.ipa`
- 大小：146,383,717 bytes
- SHA256：`7ec2668fa0bebf40b2793ec41efe53730b0de02b3df0d9844fa5c33fe1745a04`
- Xcode Debug 签名应用：ARM64 iOS device、仅系统动态依赖、4 个默认 bundle、14 组静态 qrc 与签名检查全部通过。
- Bundle ID：`org.example.krita`；Team ID：`<personal-team-id>`。
- 可复现补丁 SHA256：`32b1f82c8e0b2be671f15a3f494cae7d199284f52e214078855ddaed2dfcf247`

## 7. 2026-09-24 实机复测结果

修复后的 Xcode Debug 应用在设备 `00008142-000918E13440C01C` 上重新签名、安装并启动。随后通过 `devicectl` 捕获 180 秒实时控制台，并要求执行“新建默认文档、进入画布、画一笔”。结果如下：

- 日志越过 `KisColorSelectorTriangle` 和 `KisColorHistory` 两个原崩溃位置，继续完成画布及工具初始化。
- 观察窗口内未出现 abort、段错误或非零退出；控制台最终报告退出码 0。
- 测试后查询设备的 14 点时段 system crash logs，结果为 `0 files`。
- 仍有可选 QML 模块、字体、旧缓存路径、输入 profile 目录和 OpenGL 后台状态等非致命警告，需按后续功能测试的重要性分别处理。

本轮证据确认“点击新建即闪退”的三个已知原因已被越过。用户随后在签名 Release 应用中确认画布可用，卡顿与偶发闪退看起来已经解决；第二个连续新建文档仍保留在下一轮专项回归清单中。

## 8. 下一步验收

1. 用户确认画布可见且普通画笔能留下笔迹。
2. 连续新建第二个文档，确认 Docker 切换不会再次触发空指针。
3. 验证 Pencil 压力/倾斜、手指手势、图层、撤销与 `.kra` 保存重开。
4. 单独复现并定位已记录的 Qt iOS 触摸处理 `EXC_BAD_ACCESS`。

自动构建和控制台观察不能替代设备画面与 Pencil 行为的人工验收。
