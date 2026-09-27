# GitHub 提交准备

本仓库是源码补丁与构建支持仓库。完整 Krita checkout、Qt、目标依赖、签名应用与设备日志留在本机；仓库使用脚本获取固定源码并应用补丁。

若使用源码 ZIP 而非 Git clone，解压进入源码目录后先执行 `git init`，再运行提交候选检查。当前工作区已初始化，不需重复创建仓库。

## 提交前

```bash
python3 packaging/ios/check-repository.py --check-patches
git status --short --untracked-files=all
git diff --check
```

`--check-patches` 需要 `upstream/krita` 与 `patches/ios/baselines.json` 中的依赖源码已存在。轻量检查可在没有这些源码的全新 checkout 上运行。检查器读取已跟踪与未被忽略的文件，即使 force-add 了输出或签名文件，也会拒绝。

公开材料中的个人工作区路径与开发团队标识已替换为占位符。历史记录引用的 `logs/` 是本地证据，不随 Git 上传；公开验收结论保留在 `docs/ios/` 中。上游补丁的公开作者和邮箱作为署名保留。

## 首次提交

以下命令由维护者在确认候选清单后执行。本轮整理没有执行暂存、提交、设置远端或推送。

```bash
git add .gitignore .gitattributes .env.example .github \
  LICENSE LICENSES NOTICE.md README.md CONTRIBUTING.md docs packaging patches

python3 packaging/ios/check-repository.py
git diff --cached --stat
git diff --cached --check
git commit -m "Add experimental Krita iPadOS port and build tooling"
```

在自己的 GitHub 账号创建空仓库，把 `OWNER/REPOSITORY` 替换为实际地址，再执行：

```bash
git branch -M main
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

若本地已有 origin，检查 `git remote -v` 后选择正确远端。上游 Krita 的远端属于被忽略的嵌套 checkout，与此根仓库的 origin 分开。

## 可重现与验收边界

- 包含补丁的依赖构建读取 `patches/ios/baselines.json` 的实际提交，避免仅依赖可移动的版本标签。
- 补丁的基线 SHA、正向应用、反向应用及干净文件恢复由本地检查验证。
- 主程序和依赖曾在本地编译运行；新的聚合入口未进行全新机器的完整重建。
- CI 验证提交内容、Python/Bash 语法、文档链接和补丁格式，不证明 iOS 构建或触摸功能通过。
- 应用和 IPA 本地构建结果见[工程概况](ios/project-overview.md)与[产物记录](ios/krita-app-validation.txt)。

GitHub Actions 配置参考[官方 checkout action](https://github.com/actions/checkout)及[官方 workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)。

## 本轮整理结果（2026-09-27）

- 提交候选为 94 个源码、补丁、配置和文档文件，约 615 KiB；没有大体积产物和个人签名材料。
- Python/Bash 语法、JSON、Markdown 链接和补丁格式检查通过。
- Krita 与 8 个依赖的 11 份补丁均在临时干净基线上正向应用、反向恢复通过；没有修改现有 checkout。
- 导出纯源码目录后，在没有 Qt、依赖、构建或日志的条件下，轻量检查仍通过。
- 验证了显式包含被忽略的签名文件会被拒绝。
- 本轮未执行暂存、提交、推送或远端配置；本地 GitHub Actions 尚未在远端运行。

本地提交候选清单生成在 `.build/github-submission-manifest.json`，包含每个文件的大小与 SHA256。仅源码的 ZIP 生成在 `.build/Krita-iPadOS-source-ready.zip`，不包含 `.git/`、源码下载、日志、应用或凭证；解压后可作为独立源码目录使用。

检查日志保留在本机 `logs/github-submission-check-2026-09-27.log` 与 `logs/github-clean-export-check-2026-09-27.log`，不随仓库上传。
