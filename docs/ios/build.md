# 构建与个人签名

## 当前完整应用入口（2026-09-27）

README 的默认路径为完整 Krita Release；下方“工具链”和“未签名版本”部分保留早期独立探针记录。

新 checkout 先安装 Python 3.10+、Git、CMake、Ninja、GNU gettext（`msgfmt`、`msgmerge`）、pkg-config 和 curl，并选择完整 Xcode 的 iPhoneOS SDK。在根目录运行：

```bash
./packaging/ios/bootstrap-krita-deps.sh
./packaging/ios/configure-krita-xcode.sh
xcodebuild -project .build/krita-ios-xcode/krita.xcodeproj \
  -scheme krita -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' build
```

聚合入口按已使用的顺序调用各组件脚本，失败立即停止；不创建提交、不覆盖不同基线的 checkout。它会下载 Qt 和依赖，暂未在全新机器重跑完整过程。可按 `phase-2.md` 单独恢复失败组件。初次运行生成被 Git 忽略的 `logs/`。

签名之前设置 `KRITA_IOS_TEAM_ID`、自己的 `KRITA_IOS_BUNDLE_ID` 及 `KRITA_IOS_DEVICE_ID`，再运行 `configure-krita-xcode.sh` 和 `run-krita-device.sh`。后者现在默认 Release；需调试时显式设置 `KRITA_CONFIGURATION=Debug`。Ninja 路径的 `configure-krita.sh`、`build-krita-app.sh` 和 `package-krita.sh` 同样默认 Release，通过 `KRITA_BUILD_CONFIG=Debug` 覆盖。

生成的 `.xcodeproj` 不进 Git；本机签名参数通过环境设置，也可参考根目录 `.env.example`。当前完整应用只配置 `iphoneos`，不能把同一份 Qt device 静态库链接到模拟器。

## 工具链

本次实测：macOS 15.7.8 / arm64、Xcode 26.3 (17C529)、iOS SDK 26.2、CMake 4.4.3、Ninja、Qt 6.10.3。
最低 iPadOS 17.0 来自 [Qt 6.10 iOS 支持范围](https://doc.qt.io/qt-6.10/ios.html)。完整 Krita 的 CMake 兼容性须在阶段 2 独立验证，探针通过不代表其通过。

在工作区根目录执行 README 中命令。路径中空格已在本机真实构建验证。`build-deps.sh` 使用本地 `.venv` 安装 aqtinstall 3.3.0，再从 Qt 仓库取得同版本 desktop/ios qtbase；不安装到系统目录。不盲目编译其余 Krita 依赖。
已有 Qt kit 可设置 `QT_IOS_PREFIX` 和 `QT_HOST_PATH`。也可覆盖 `QT_VERSION`、`IOS_BUILD_DIR`、`KRITA_IOS_MIN_VERSION`（不能低于 17）。非默认 kit 的部署版本要求需另行核对。

Qt 静态插件由 `qt_finalize_executable` 生成导入代码。本次链接包含 QIOSIntegrationPlugin 和 JPEG/ICO 插件；Qt、Widgets 和平台插件以静态库链接，系统框架由 iOS 提供。

## 未签名版本

```bash
./packaging/ios/configure.sh
./packaging/ios/build-device.sh
```

默认 `KRITA_IOS_SIGN=0`，构建参数为 `CODE_SIGNING_ALLOWED=NO`。成功产物不能直接安装到普通实体设备。不要把 macOS 探针当成 iOS 应用。

## 个人签名

在 Xcode Settings → Accounts 中添加自己的 Apple 账号，选择个人或已有开发团队，连接并信任 iPad，在设备设置启用 Developer Mode。证书、开发描述文件、个人账号能力和期限以 Xcode 实际显示为准。

```bash
export KRITA_IOS_TEAM_ID="XXXXXXXXXX"
export KRITA_IOS_BUNDLE_ID="org.yourname.krita.probe"
./packaging/ios/configure.sh
KRITA_IOS_SIGN=1 ./packaging/ios/build-device.sh
```

然后在 Xcode 打开 `.build/ios-probe/KritaIOSProbe.xcodeproj`，选择 KritaIOSProbe scheme 和目标 iPad，Run。若 Xcode 提示签名或设备信任操作，按提示处理。
关键配置保存在 CMake 和 plist 中；不要依靠手工修改 `.pbxproj` 保留配置。

也可在签名成功后用开发工具安装（把占位符替换为 `xcrun devicectl list devices` 的设备 ID）：

```bash
xcrun devicectl device install app --device DEVICE_ID ".build/ios-probe/Debug-iphoneos/KritaIOSProbe.app"
xcrun devicectl device process launch --device DEVICE_ID org.yourname.krita.probe
```

本轮未执行签名或安装，用户明确选择未签名版本。

## 日志与复现

- `logs/configure-ios.log`：最终配置输出。
- `logs/build-device.log`：Xcode 完整构建输出。
- `.build/ios-probe/CMakeFiles/CMakeConfigureLog.yaml`：编译器探测细节。
- `./packaging/ios/test-host.sh`：macOS offscreen 自动测试。
- App 的 Documents/probe-events.txt：运行期事件证据，下一次启动覆盖；验收后从 Files 导出保存。

Codex 沙盒首次阻止 Xcode 缓存/服务访问时，需允许构建命令在正常 macOS 开发环境运行；不应通过伪造编译器结果绕过。

## 完整 Krita（阶段 2）

先按 [阶段 2 记录](phase-2.md) 准备目标依赖，再运行：

```bash
./packaging/ios/configure-krita.sh
./packaging/ios/build-krita-app.sh
./packaging/ios/package-krita.sh
```

打包输出 `.build/krita-ios-install/krita.app` 和 `.build/Krita-iPadOS-unsigned.ipa`。
两者均未做个人签名，不能直接安装到普通设备。使用此前为探针签名的工具或现有个人签名流程签名 IPA；签名工具需要使 Bundle ID、描述文件与签名身份一致。
当前默认 Bundle ID 为 `org.example.krita`，最低 iPadOS 17.0，iPad ARM64 横屏。
如需预先指定自己的标识：

```bash
KRITA_IOS_BUNDLE_ID=org.yourname.krita ./packaging/ios/configure-krita.sh
./packaging/ios/build-krita-app.sh
./packaging/ios/package-krita.sh
```

请安装打包目录中的应用。`.build/krita-ios/bin/krita.app` 是链接输出，未复制完整的安装资源。
签名后的应用可以通过 Xcode 的 Devices and Simulators 安装；也可用以下命令，路径须替换为实际签名后应用路径：

```bash
xcrun devicectl device install app --device DEVICE_ID /absolute/path/to/signed/krita.app
xcrun devicectl device process launch --device DEVICE_ID org.yourname.krita
```

完整 Krita 的 Xcode 工程已可生成。默认仍关闭签名：

```bash
./packaging/ios/configure-krita-xcode.sh --fresh
```

工程位于 `.build/krita-ios-xcode/krita.xcodeproj`，主 scheme 为 `krita`。Xcode 构建后会自动将 Krita 的 `share` 运行时数据复制进 `.app`。若要用自己的团队直接 Run 到 iPad，重新配置时同时提供唯一 Bundle ID 和 Team ID：

```bash
export KRITA_IOS_BUNDLE_ID="org.yourname.krita"
export KRITA_IOS_TEAM_ID="XXXXXXXXXX"
./packaging/ios/configure-krita-xcode.sh --fresh
```

脚本只有在显式提供 `KRITA_IOS_TEAM_ID` 时才允许最终的 `krita` 应用 target 签名；未提供时保持 `CODE_SIGNING_ALLOWED=NO`。静态库和静态插件始终保持不签名，避免 Xcode 对数百个中间 target 报 “requires a development team”。打开工程后选择 `krita` scheme 和目标 iPad，再 Run。

完整工程很大，在 Xcode 图形界面修改 Build Settings 可能长时间无响应。可以退出 Xcode 后，用脚本增量刷新工程并完成构建、签名检查、安装和启动，无需手工修改生成的 `.pbxproj`：

```bash
export KRITA_IOS_TEAM_ID="XXXXXXXXXX"
export KRITA_IOS_DEVICE_ID="000081..."
export KRITA_IOS_BUNDLE_ID="org.yourname.krita"
./packaging/ios/run-krita-device.sh
```

设备标识可从 `xcrun devicectl list devices` 或 Xcode 的 Devices 页面取得。脚本会先重新运行 CMake，但不会删除已有构建产物，随后由 Xcode 增量构建。脚本把完整输出保存到 `logs/krita-xcode-signed-device.log`。若只需安装而不自动启动，可同时设置 `KRITA_IOS_LAUNCH=0`。

2026-09-24 已用 Team ID `<personal-team-id>`、Bundle ID `org.example.krita` 完成 Debug 真机构建、严格签名校验、安装和启动。最终应用的 `CODE_SIGNING_ALLOWED=YES`，代表性静态插件 `krita_colorspaces_extensions` 的值为 `NO`。签名证书链、Team ID 和 Bundle ID 均可由 `codesign` 读取。脚本只对 `CSSMERR_TP_NOT_TRUSTED` 这一特定本机证书链信任错误发出警告并继续用设备验证，其他签名错误仍会终止。

运行验证按 [完整 Krita 真机验收表](krita-device-checklist.md) 记录。主窗口、画布、150% GUI 缩放、Files、Pencil 和保存恢复不能仅凭编译结果判定通过。
