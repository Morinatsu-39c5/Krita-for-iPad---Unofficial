# Krita for iPadOS

将 [KDE Krita](https://github.com/KDE/krita) 移植到 iPadOS 的实验性工程，保留原版 Qt Widgets 界面、绘画核心和内置插件。**本项目为非官方移植，不是 KDE 正式发行版。**

An experimental, unofficial iPadOS port of Krita. This repository contains the port patch, dependency patches, build scripts and validation records. It fetches pinned upstream sources locally rather than vendoring the Krita repository.

## 当前状态

截至 2026-09-27，已完成 ARM64 真机 Release 构建、开发签名、iPad 安装和启动。固定基线为 Krita `6.1.0-prealpha`：

```text
3a9b5ef03f8312b6f630fc5d475e1692598e8719
```

- 静态注册 147 个 Krita 插件、14 组 qrc，默认资源数据库和主界面已在真机运行。
- 新建文档、Pencil 触控生命周期及栅格画布的已报告崩溃完成修复；用户测试 Release 后认为画布卡顿和偶发闪退已改善。
- `.kra` 保存写入 Files 可见的应用 `Documents`；Pencil 双击切换橡皮，Pencil Pro 捏压调用轮盘。
- 已实施非文本键盘保护、异步关闭确认与系统 picker 保护，具体触摸行为仍需持续实机回归。
- 简体、繁体、英语的菜单和设置正文使用真实 KI18n 在真机查询并通过比较；完整语言切换及界面布局仍需人工验收。

尚未完整验收压感/倾斜、资源导入、复杂格式、长期绘画、批量关闭及恢复流程。GUI 150% 可配置缩放尚未在完整应用接入。Python、外部可执行插件及若干可选格式/引擎暂缺。详见[工程概况](docs/ios/project-overview.md)与[真机验收表](docs/ios/krita-device-checklist.md)。

## 构建

需要 Apple Silicon macOS、完整 Xcode/iPhoneOS SDK、Python 3.10+、Git、CMake、Ninja、GNU gettext 的 `msgfmt`/`msgmerge`、pkg-config 和 curl。当前验证的 Qt 版本为 **6.10.3**，目标为 **iPadOS 17.0+、ARM64 真机**；此工程不支持直接用同一份 Qt 静态库构建模拟器。

在仓库根目录执行：

```bash
./packaging/ios/bootstrap-krita-deps.sh
./packaging/ios/configure-krita-xcode.sh

xcodebuild -project .build/krita-ios-xcode/krita.xcodeproj \
  -scheme krita -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' build
```

工程生成在 `.build/krita-ios-xcode/krita.xcodeproj`，应用生成在 `.build/krita-ios-xcode/bin/Release/krita.app`。未提供 Team ID 时保持未签名。初次依赖编译耗时较长，失败即停止，可逐项恢复。完整顺序与 Ninja 未签名 IPA 入口见[构建指南](docs/ios/build.md)。各组件在本地工作区完成过构建；新增聚合入口尚未重跑全新机器的完整下载和编译。

## 个人签名和安装

使用自己的开发团队、Bundle ID 和 iPad 标识，不将这些信息提交到仓库：

```bash
export KRITA_IOS_TEAM_ID="YOUR_TEAM_ID"
export KRITA_IOS_BUNDLE_ID="org.yourname.krita"
export KRITA_IOS_DEVICE_ID="YOUR_IPAD_ID"
export KRITA_CONFIGURATION=Release

./packaging/ios/configure-krita-xcode.sh
./packaging/ios/run-krita-device.sh

python3 packaging/ios/package-krita-ipa.py \
  .build/krita-ios-xcode/bin/Release/krita.app \
  .build/Krita-iPadOS-Release-signed.ipa
```

也可将 [.env.example](.env.example) 复制为本机 `.env`，填写后用 `source .env` 加载；脚本不会自动读取 `.env`。签名有效期和设备范围取决于自己的 Apple 开发账号。

## 仓库结构与检查

| 路径 | 内容 |
|---|---|
| `patches/ios/krita-ipados.patch` | 相对于固定 Krita 基线的完整移植补丁，包含新增源文件 |
| `patches/ios/dependencies/`、`*-no-process.patch` | 依赖的交叉编译和平台补丁 |
| `patches/ios/baselines.json` | 补丁对应的源码仓库和实际提交 |
| `packaging/ios/` | 源码获取、依赖准备、配置、打包与验证脚本 |
| `packaging/ios/probe/` | 独立平台探针，用于早期验证 |
| `docs/ios/` | 当前状态、构建说明、问题分析与历史验收记录 |

`upstream/`、`.qt/`、`.deps/`、`.build/`、`logs/`、签名材料及设备报告仅保留在本机。生成的 Xcode 工程包含机器路径，使用构建脚本重新生成。

```bash
# 不需要 Qt 或设备：检查提交候选、脚本语法、文档链接和补丁格式。
python3 packaging/ios/check-repository.py

# 已下载固定源码时：在临时干净基线上验证所有补丁正向和反向应用。
python3 packaging/ios/check-repository.py --check-patches

# 准备宿主 Qt、KI18n 和应用后可运行功能回归。
python3 packaging/ios/test-popup-regressions.py
python3 packaging/ios/test-localization-regressions.py
```

GitHub Actions 运行轻量仓库检查；不运行 Apple 签名、完整 iOS 编译或真机测试。贡献流程见[CONTRIBUTING.md](CONTRIBUTING.md)，首次提交步骤见[GitHub 提交准备](docs/github-submission.md)。

## 文档

- [工程概况](docs/ios/project-overview.md) · [构建与签名](docs/ios/build.md)
- [正文翻译与简繁切换修复](docs/ios/localization-repair-2026-09-27.md)
- [关闭确认与系统 picker 修复](docs/ios/popup-and-picker-repair-2026-09-26.md)
- [Pencil、键盘与语言记录](docs/ios/input-gesture-and-keyboard-plan-2026-09-24.md)
- [源码评审](docs/ios/project-review-2026-09-23.md) · [依赖调查](docs/ios/dependencies.md)

## 许可证

原创移植脚本、探针及文档默认使用 **GPL-3.0-or-later**，原有文件与依赖补丁保留各自许可证及作者信息。参见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md)。
