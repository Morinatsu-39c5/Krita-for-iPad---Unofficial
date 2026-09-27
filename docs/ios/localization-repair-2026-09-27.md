# Krita 正文未翻译与简繁切换修复

报告日期：2026-09-26；修复和最终验证跨至 2026-09-27。所有修改保留在本地，未暂存、未提交。

## 用户报告与诊断

用户截图 `IMG_0168.PNG` 中，“确定”“取消”“搜索”已是中文，但 File/Edit 菜单、Performance 页面及 Memory Limit 等设置正文仍是英语。

已确认安装包包含有效的 `zh_CN`、`zh_TW` Krita `.mo` 与 KDE `.qm`。设备的语言配置曾为 `zh_CN`；读取配置和目录中有文件只能证明设置与打包，不能证明界面实际加载了翻译。Qt/KDE 部分按钮通过 `.qm` 翻译，Krita 大部分正文通过 KI18n/gettext `.mo` 翻译，两条路径独立。

启动诊断通过真实 `i18n()` 查询取得修复前证据：语言为 `zh_CN`、目录指向 app 内 `share/locale`，但 `Performance` 和 `Memory Limit:` 都原样返回英语。证据：`logs/krita-localization-before-2026-09-26.json`。

## 已确认的两个原因

### 翻译目录注册太晚

原来在 `KisApplication` 构造和 `installTranslators()` 之后才注册 `krita` 的 locale 目录。iOS 的 `QStandardPaths::GenericDataLocation` 不搜索 app 的 `share/locale`；首次查找失败时，KI18n 将空目录缓存到 `(domain, language)` 对应的 `KCatalog`。后续 `addDomainLocaleDir()` 不清理已创建的 catalog，因此正文继续显示英语。

现在在临时 `QCoreApplication` 取得 bundle 根路径后立即注册 `krita`、`ki18n6` 和 `kcolorscheme6`，并设置应用 domain；执行点早于正式 `KisApplication` 构造及 translator 安装。原有语言选择、系统语言推导和 Qt 翻译逻辑继续使用。

第一次提前注册的真机报告已返回繁体中文：`Performance → 效能`、`Memory Limit: → 記憶體限制：`、`&File → 檔案(&F)`。证据：`logs/krita-localization-early-registration-2026-09-26.json`。

### 静态 gettext 链接探测漏掉传递依赖

三语言回归进一步发现：当前繁体中文可以使用，但显式请求 `zh_CN` 仍返回繁体。KI18n 的 `HAVE_NL_MSG_CAT_CNTR` 检测错误地为 0，翻译时没有增加 GNU gettext 的 `_nl_msg_cat_cntr`，导致 LANGUAGE 改变后复用旧缓存。

`FindLibIntl.cmake` 的独立链接测试只带了 `libintl.a`，漏掉 CoreFoundation 与 iconv；失败日志依次显示 `_CFLocaleCopyPreferredLanguages`、`_iconv` 和 `_iconv_open` 未定义。主程序因为 Qt 的完整链接依赖而可以链接，这使缺陷只表现为运行时切换错误。

依赖补丁 `patches/ios/dependencies/ki18n/0001-ios-static-gettext-link-probe.patch` 为 iOS 探测补齐 CoreFoundation 与 iconv。重新检测实际成功，没有强制写死检测结果。重新构建的 `.deps/ios/lib/libKF6I18n.a` 包含 `__nl_msg_cat_cntr` 未定义引用，生成配置为 `HAVE_NL_MSG_CAT_CNTR 1`。补丁由现有 `build-krita-deps.sh ki18n` 自动应用。

已有配置缓存可这样重新检测：

```sh
bash packaging/ios/build-krita-deps.sh ki18n -U HAVE_NL_MSG_CAT_CNTR
```

## 回归与验收范围

`python3 packaging/ios/test-localization-regressions.py` 从生产源码提取注册 helper，构建固定版本的宿主 KI18n，并直接读取当前 app 的 `.mo`。检查 iOS 库确实启用了 gettext 缓存刷新，然后使用真实 KI18n/gettext 验证：

1. 首次失败后再注册目录，会持续返回英语，复现原故障。
2. 提前注册后，销毁临时 application 并创建正式 application，中文 catalog 仍可使用。
3. 简体、繁体的设置正文、菜单及带 context 的 Copy action 与打包 catalog 一致。
4. 英语仍返回英语；注册 helper 不修改 numeric locale。

日志：`logs/krita-localization-host-regression-2026-09-27.log`。

真机诊断仅在启动环境包含 `KRITA_IOS_LOCALIZATION_DIAGNOSTICS=1` 时运行，记录当前 UI 语言和三种语言的实际 KI18n 返回值到 `Library/Caches/Krita/ios-localization.json`。不会修改用户的语言偏好。正常启动不执行该诊断。

`verify-krita-app.py` 新增 `--localization-report` 参数，把真机报告与 app 内真实 catalog 比较。三套菜单和设置文本必须逐项一致；该检查能拒绝“简体样本实际返回繁体”的中间版本。

```sh
python3 packaging/ios/verify-krita-app.py \
  .build/krita-ios-xcode/bin/Release/krita.app \
  --build-dir .build/krita-ios-xcode --signing signed \
  --localization-report logs/krita-localization-runtime-verified-2026-09-27.json
```

自动查询验证的是界面同一套翻译调用。完整界面布局、语言选择后完全退出再启动、全部菜单与 Docker 的人工验收仍需在 iPad 上复测。catalog 本身尚未翻译的词条仍可能显示英语。

## 最终产物

已完成最终 Release 构建、签名、覆盖安装和普通启动。Bundle ID `org.example.krita`，Team ID `<personal-team-id>`；诊断启动 PID 6697，随后移除诊断环境的普通启动 PID 6698。设备当前 UI 语言为 `zh_TW`，没有更改用户语言设置。

普通启动后的进程查询确认 PID 6698 仍运行；证据：`logs/krita-localization-running-2026-09-27.json`。

三语言真机结果：

| 查询 | 简体 zh_CN | 繁体 zh_TW | 英语 en_US |
|---|---|---|---|
| Performance | 性能 | 效能 | Performance |
| Memory Limit: | 内存分配上限： | 記憶體限制： | Memory Limit: |
| &File | 文件(&F) | 檔案(&F) | &File |

应用门禁（ARM64/iOS device/signed/仅系统动态依赖/4 个 bundle/14 个 qrc/catalog）及运行时报告逐项比较：PASS。IPA ZIP CRC、plist、执行权限和逐文件内容一致性：PASS。补丁反向应用及源码 diff 检查：PASS。

| 产物 | 大小 / SHA256 |
|---|---|
| `.build/krita-ios-xcode/bin/Release/krita.app` | 1466 files，259079020 bytes；主程序 `4bec67f33dd3437c41093b840b16dfe350f41c2c84757eec97b2f14c5a96bfd9` |
| `.build/Krita-iPadOS-Release-signed.ipa` | 118793585 bytes；`5b5b03eb0789465166a446df473a9df8714122f842356d71ed5047a34d633185` |
| `patches/ios/krita-ipados.patch` | 142620 bytes；`b73335162ee2e785a2d9a51364fbea3df3a0a3410743157c5e348f5c734bd826` |
| `patches/ios/dependencies/ki18n/0001-ios-static-gettext-link-probe.patch` | 964 bytes；`6b3dc485e36b2c7d6bb430ddcc7241bc3f512f5dff22a03d6235e53e7ee0cd0a` |

证据文件：

- `logs/krita-localization-final-build-2026-09-27.log`：最终 BUILD SUCCEEDED。
- `logs/krita-localization-ki18n-fixed-rebuild-2026-09-27.log`：修复依赖的配置、构建和安装。
- `logs/krita-localization-host-regression-2026-09-27.log`：宿主真实 KI18n 回归 PASS。
- `logs/krita-localization-gate-negative-2026-09-27.log`：错误简体报告被门禁拒绝。
- `logs/krita-localization-runtime-verified-2026-09-27.json`：三语言实际返回值。
- `logs/krita-localization-app-validation-2026-09-27.log`：应用与真机翻译报告门禁 PASS。
- `logs/krita-localization-verified-install-2026-09-27.json`、`logs/krita-localization-normal-launch-2026-09-27.json`：安装与普通启动成功。
- `logs/krita-localization-ipa-validation-2026-09-27.log`：签名 IPA 完整性 PASS。
- `logs/krita-localization-artifacts-2026-09-27.json`：产物大小与哈希。

本轮没有修改 Qt、Pencil、保存或关闭弹窗实现。历史未签名 IPA 仍是 2026-09-24 Debug 快照；最新签名 Release IPA 包含前轮弹窗修复与本轮翻译修复。
