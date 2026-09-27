# Krita iPadOS 真机启动问题记录

日期：2026-09-23  
状态：已确认现象并完成只读检查，尚未修复。  
用户要求：先确认问题，不解决；不提交 Git。

## 测试对象与证据

- 设备：用户的 iPad Pro M5。
- 应用：Krita 6.1.0-prealpha，源码基线 `3a9b5ef03f8312b6f630fc5d475e1692598e8719`，加本工作区 iPadOS 补丁。
- 本地交付产物：`.build/krita-ios-install/krita.app`、`.build/Krita-iPadOS-unsigned.ipa`；用户已完成真机安装并提供截图。
- 本地构建方式：CMake/Ninja，ARM64 实体 iPad，最低 iPadOS 17.0。
- 会话中曾收到 `IMG_0150.PNG`、`IMG_0151.PNG`、`IMG_0152.PNG`；2026-09-24 收尾检查时 Downloads 中的原件已不存在，工作区没有副本，因此这里只保留截图中已转录的错误信息，不提供失效链接。

截图证明应用已启动并显示 Krita 启动画面，在 “Loading resources...” 阶段弹出错误。尚未证明进入主窗口或创建画布。弹窗提示 “Krita will quit now.”；截图本身不证明按下 OK 后的实际退出过程。

## 问题一：资源数据库初始化失败（当前启动阻塞）

### 已确认的现象

首张截图中的关键错误为：

```text
Could not initialize the resource cache database. Statement error:
Could not find SQL file :/create_version_information.sql
Error executing SQL

Krita will quit now.
```

`:/create_version_information.sql` 是 Qt 内嵌资源路径，不是 Files、iCloud 或应用沙盒中的普通文件路径。

### 只读检查证据

1. `upstream/krita/libs/resources/sql.qrc` 包含 `sql/create_version_information.sql`，别名为 `create_version_information.sql`，资源前缀为 `/`。
2. `upstream/krita/libs/resources/CMakeLists.txt` 使用 `qt_add_resources(kritaresources_LIB_SRCS sql.qrc)` 编译该资源。
3. 本地静态库 `.build/krita-ios/lib/libkritaresources.a` 的符号表包含 `qInitResources_sql()` 和 `qCleanupResources_sql()`。
4. 本地最终可执行文件 `.build/krita-ios-install/krita.app/krita` 的符号表中未找到上述两个符号。
5. `KisResourceCacheDb.cpp` 在 SQL 文件加载失败时生成 “Could not find SQL file” 错误，并将其作为资源缓存数据库初始化的 Statement error 报告，与截图一致。

### 当前判断及边界

截图与本地构建证据高度指向：改为静态链接后，SQL 内嵌资源对象没有被带入最终可执行文件，导致初始化数据库所需的 SQL 不可用。

这是目前最有证据支持的根因判断；尚未通过修复后的真机运行闭环验证，也未提取用户签名安装后的可执行文件进行比对。当前没有证据将首个错误归因于沙盒写入权限、iCloud 访问或资源包损坏。

## 问题二：资源同步与笔尖元数据错误

后两张截图报告：

- 无法将沙盒内 `Library/Application Support/krita/` 与数据库同步。
- 无法将 `Krita_3_Default_Resources.bundle`、`Krita_4_Default_Resources.bundle`、`Krita_Artists_SeExpr_examples.bundle`、`RGBA_brushes.bundle` 与数据库同步。
- `Could not synchronize memory with the database`。
- `Could not access brush tip metadata`。

这些错误很可能是数据库初始化失败后的连锁结果，尚未证明是独立故障。不能仅据这些信息认定四个资源包都损坏、笔刷引擎全部不可用或沙盒路径不可写。需要先消除数据库初始化阻塞，之后才能判断是否仍有独立的资源同步问题；本轮未执行修复。

## 问题三：长错误弹窗的显示体验

错误弹窗很窄且接近屏幕全高，长路径和文件名大量换行，需要滚动才能查看完整内容。截图可以确认可读性问题；它不是当前数据库初始化失败的首因，也不足以据此判断整个主界面的布局和缩放情况。

## 现有验证的遗漏

此前的打包检查确认了应用架构、iOS 平台、系统动态依赖、外部默认资源包完整性和 IPA 结构，但没有检查 SQL 内嵌资源是否实际进入最终可执行文件，也没有执行完整应用的真机启动测试。

因此，“资源包完整性检查通过”不能等同于“启动所需的全部资源可用”。本次截图已经确认完整应用当前未通过主窗口启动验收；探针的真机测试结果不能替代该项验收。

## Xcode 工程位置与独立阻塞

### 已生成的探针工程

`.build/ios-probe/KritaIOSProbe.xcodeproj`

实际路径：

```text
.build/ios-probe/KritaIOSProbe.xcodeproj
```

这是独立的 Qt Widgets 探针工程，不是完整 Krita 工程。

### 完整 Krita 工程尚未生成成功

尝试生成目录：

```text
.build/krita-ios-xcode
```

配置在 Krita 根 `CMakeLists.txt` 的 `check_cxx_symbol_exists(QT_HAS_ENTER_LEAVE_PATCH ...)` 检测阶段中断。关键报错涉及：

```text
$<TARGET_OBJECTS:Qt6::Gui_resources_1>
```

CMake 无法在 Xcode 生成器的检测工程中正确求值/导出该资源目标，随后报告目标不存在。日志见 `logs/krita-xcode-configure.log`。

目录中的 `CompilerId*.xcodeproj` 只是编译器识别测试工程，不能用来构建完整 Krita。当前交付的完整应用由 CMake/Ninja 构建。

Xcode 工程生成错误与真机 SQL 内嵌资源缺失应分别跟踪；当前没有证据证明两者是同一个故障。

## 本轮操作范围

仅记录截图现象、既有源码及产物检查证据。未修改应用源码、未重新配置或构建、未重新打包、未安装应用、未暂存或提交 Git。
