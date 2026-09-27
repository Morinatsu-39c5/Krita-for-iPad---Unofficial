# iPadOS 沙盒保存路径与弹窗无响应修复

更新日期：2026-09-24  
代码状态：修改保留在本地，未暂存、未提交。

## 1. 可访问目录

Krita 在 iPadOS 上可直接写入的用户文档目录是：

```text
/var/mobile/Containers/Data/Application/<当前安装 UUID>/Documents
```

该目录在“文件”App 中显示为：

```text
在我的 iPad 上/Krita
```

安装 UUID 由系统分配，卸载重装后会变化，代码和用户操作都不应保存或手工填写完整绝对路径。应用私有的 `Library/Application Support` 用于资源数据库和配置，不是用户文档保存位置。

应用 `Info.plist` 已包含 `UIFileSharingEnabled=true` 和 `LSSupportsOpeningDocumentsInPlace=true`，因此 `Documents` 会暴露给“文件”App。

## 2. 问题原因

桌面 Krita 的保存流程会读取上次目录，并在首次保存时回退到 `PicturesLocation`。在 iOS 上，上次目录可能包含旧安装的 UUID，`PicturesLocation` 也不是本移植版本约定的 Files 可见目录。

更直接的问题是保存使用同步的 `QFileDialog::exec()`。Qt 6.10.3 的 iOS 原生文件对话框不支持 `AcceptSave`，Krita 因而使用 Qt Widgets 文件对话框；同步执行会进入嵌套模态事件循环，表现为弹窗已经出现但触控无响应。

## 3. 当前修复

- 打开/导入对话框从当前安装的 `Documents` 开始，不再复用旧安装 UUID。
- 新文档首次保存不再打开同步文件对话框，直接保存为 `Documents/Untitled.kra`。
- 同名文件存在时自动使用 `Untitled 2.kra`、`Untitled 3.kra` 等名称，避免覆盖。
- 对已有文档执行“另存为”会在 `Documents` 中建立 `名称 Copy.kra`，同样自动避开重名。
- 恢复文档的默认路径也改为 `Documents`。
- 桌面平台行为保持不变。

这一步解决 `.kra` 在应用沙盒内的可靠保存。任意 iCloud Drive 或第三方文件提供商的目标目录仍需后续接入异步 `UIDocumentPickerViewController` 导出流程；“导出”菜单的同步格式选择也不在本次修复范围内。

## 4. 构建验证

- `KisMainWindow.cpp` 已完成 iPadOS ARM64 增量编译和最终链接。
- Debug 应用门禁通过：ARM64、iOS device、未签名、仅系统动态依赖、4 个默认资源包和 14 组静态 qrc 均通过。
- 未签名 IPA 已重新生成并通过 ZIP CRC、plist、可执行权限和逐文件内容检查。
- 真机保存、关闭、从“文件”App 查看并重新打开仍需使用最新签名应用验证。

## 5. 真机验收步骤

1. 新建画布并画一笔。
2. 选择“文件 → 保存”；不应再出现无响应的“另存为”弹窗。
3. 打开“文件 → 在我的 iPad 上 → Krita”，确认出现 `Untitled.kra`。
4. 回到 Krita 再画一笔并保存，确认仍写入同一文档。
5. 再新建一个画布并保存，确认生成 `Untitled 2.kra`，未覆盖第一个文件。
6. 关闭文档，再从 Krita 打开上述 `.kra`，检查画布、图层和笔迹。
