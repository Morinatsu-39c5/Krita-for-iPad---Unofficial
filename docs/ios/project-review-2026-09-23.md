# Krita iPadOS 工作区问题记录（2026-09-23）

本文是对整个工作区的独立检查记录。**只记录问题，不包含任何修复**；未修改源码、未重新构建、未重新打包、未签名、未暂存或提交 Git。

复核对象：工作区 `<workspace>`，状态截止 2026-09-23 17:58 PDT。

## 0. 复核范围与方法

| 项目 | 说明 |
|---|---|
| 方式 | 全程只读；`nm`/`otool`/`codesign`/`lipo`/`unzip -t`/`shasum`/`git` 直接检查产物与仓库 |
| 已检查 | 目录与体积、Git 状态、上游改动与补丁一致性、构建脚本与校验脚本、依赖前缀、静态归档、最终可执行文件符号与字符串、应用包与 IPA、日志、全部 `docs/ios/` 文档 |
| 未检查 | 未验证真机行为；未验证绘画、压感、Files、保存恢复等功能；未做 Release 构建对比 |
| 副作用 | 检查期间 `python3 -m py_compile` 生成的 `packaging/ios/__pycache__/` 已删除，工作区恢复原状（`patches/ios/krita-ipados.patch` 的 mtime 仍为 09-23 16:36，内容未变） |

## 1. 结论摘要

1. 文档中的**技术结论与全部关键数字经得起复核**：产物真实、校验和一致、数量吻合、"SQL 内嵌资源未进入最终可执行文件"的判断成立。
2. 存在一项文档完全未提及的交付问题：**当前 IPA 是 Debug 构建**（RV-01）。
3. 存在一项比文档描述**范围更大**的根因：**所有编译进静态库的 qrc 资源整体丢失**，SQL 只是其中最致命的一个（RV-02）。只修 `sql.qrc` 会留下同类问题。
4. 校验链路本身不可靠：补丁导出脚本与打包校验脚本都不能保证失败可见（RV-04、RV-05、RV-06）；依赖 pin 的保护实际无效（RV-07）。
5. 驱动整份问题记录的**唯一真机直接证据（3 张截图）已不在文档所写路径**（RV-03）。
6. 若干文档状态陈述停留在阶段 2 之前，与最新记录互相矛盾（RV-08）。

## 2. 已复核确认正确的部分

以下各项均为本次独立复跑得到，不是转述文档。

| 项目 | 复核结果 |
|---|---|
| 源码基线 | `git -C upstream/krita rev-parse HEAD` = `3a9b5ef03f8312b6f630fc5d475e1692598e8719` |
| 上游改动 | 36 个已跟踪文件被修改 + 4 个未跟踪新文件（`upstream/krita/packaging/ios/`），共 40 项 |
| 补丁一致性 | `patches/ios/krita-ipados.patch` 与"当前 `git diff` + 未跟踪新文件"**逐字节相同**；75,248 字节，sha256 `559b3a29d35fbb085eb40f4cce0eb4dbd9e04bd77e8d78bbf35526e24cae917b`；含 40 个 `diff --git` 段 |
| 静态归档 | `docs/ios/krita-core-libraries.txt` 的 194 个归档逐个体检：`arm64` + `platform 2` 全部通过，0 失败、0 缺失 |
| 目标依赖库 | `.deps/ios/lib/*.a` = 32 个，与 `docs/ios/target-libraries.txt` 的 32 行一致 |
| 插件导入 | `.build/krita-ios/krita/krita_ios_plugins.cpp` 中 `Q_IMPORT_PLUGIN` 恰为 **147** 个 |
| 应用包 | `.build/krita-ios-install/krita.app` 共 602 个文件，文件长度合计 455,444,380 字节；主可执行文件 382,009,816 字节，Mach-O arm64 |
| IPA | 146,165,071 字节；sha256 `7e8a9ac80f0b56924c328c9547bdf92b9b8bb679d8cbf09814f2dd0fbbf2d8ce`（与文档完全一致）；`unzip -t` 通过，602 项 |
| 资源包 | 4 个默认 bundle 均存在且 `unzip -t` 通过（CRC 无损坏） |
| 签名与依赖 | `codesign -dv` 报告 `code object is not signed at all`；`otool -L` 仅 `/usr/lib/*` 与 `/System/Library/Frameworks/*` |
| 包内清洁度 | 应用包内无额外 `*.dylib`/`*.so`/可执行文件，无符号链接，无 Python 残留 |
| 平台标记 | `LC_BUILD_VERSION platform 2`（iOS）、`minos 17.0`、`sdk 26.2` |
| **核心诊断** | `sql.qrc` 别名 `create_version_information.sql`、前缀 `/` 正确；`libkritaresources.a` 导出 `qInitResources_sql`/`qCleanupResources_sql`；最终可执行文件 `nm -a` 中这两个符号 **0 次命中**，且二进制内不存在 `create_version_information` 字符串 → 文档"SQL 资源未进入最终程序"的判断成立 |
| Xcode 阻塞 | `logs/krita-xcode-configure.log` 确实在 `check_cxx_symbol_exists(QT_HAS_ENTER_LEAVE_PATCH ...)` 处因 `$<TARGET_OBJECTS:Qt6::Gui_resources_1>` 求值失败中断；`.build/krita-ios-xcode` 内只有 `CMakeFiles/4.4.3/CompilerId*.xcodeproj` |
| 工具链 | macOS 15.7.8 (24G812) / Xcode 26.3 (17C529) / iOS SDK 26.2 / CMake 4.4.3 / Ninja 1.13.2 / Qt 6.10.3，全部与文档吻合 |
| 依赖版本 | KF6 6.18.0、Exiv2 0.28.8、Expat 2.7.5、Fontconfig 2.16.0、FriBidi 1.0.16、HarfBuzz 12.3.2、lcms2 2.19、PNG 1.6.50、QuaZip 1.4、Boost 1.87.0、Eigen 5.0.1、xsimd 14.1.0 与 `phase-2.md` 一致；FreeType 确为 `-DFT_DISABLE_HARFBUZZ=ON` 的 bootstrap 构建 |
| 依赖缺失 | MyPaint、TIFF、OpenEXR、OpenColorIO、WebP、HEIF、JPEG XL、OpenJPEG、Poppler、FFTW、KSeExpr 确实未出现在 `.deps/` |

---

## 3. 问题清单

### P0 —— 影响交付判断

#### RV-01　交付物是 Debug 构建，文档完全未提

**证据**

- `.build/krita-ios/CMakeCache.txt`：`CMAKE_BUILD_TYPE:STRING=Debug`。
- `packaging/ios/configure-krita.sh:10` 硬编码 `-DCMAKE_BUILD_TYPE=Debug`。
- `packaging/ios/build-krita-app.sh:4`、`packaging/ios/package-krita.sh:7` 的 `KRITA_BUILD_CONFIG` 默认值都是 `Debug`。
- `.build/krita-ios/build.ninja` 中编译命令行**只有 `-g`，没有任何 `-O*`**；`DNDEBUG` 出现 0 次（即断言全部生效）。
- `LINK_LIBRARIES` 中链接的是 Qt debug 静态库：`QtGui.framework/QtGui_debug`、`QtWidgets_debug`、`QtCore_debug`、`QtQml_debug`、`QtSql_debug` 等；二进制调试映射里可见 `.qt/6.10.3/ios/lib/QtQml.framework/QtQml_debug(qv4sqlerrors.cpp.o)`。
- 与之相反，依赖全部是优化构建：`build-krita-deps.sh:60` 使用 `-DCMAKE_BUILD_TYPE=Release`，fontconfig/fribidi 使用 `--buildtype release`，gettext 使用 `-O2`。

**影响**

- 382 MB 可执行文件 / 146 MB IPA，主要来自未优化代码与调试信息。
- 启动速度、内存占用、画布刷新、笔刷延迟等**一切性能结论无效**，必须用 Release 重测后才能对外表述。
- 断言与调试路径全部开启，行为与最终发布形态不同。
- 文档（`README.md`、`phase-2.md`、`build.md`）没有任何一处提到构建类型，读者会默认拿到的是发布级产物。

**边界**：首次真机 bring-up 用 Debug 本身是合理选择；问题在于**没有记录**，且文档中的"功能恢复与性能优化（阶段 5）"没有把 Release 重建列为前置条件。

#### RV-02　静态库中的 qrc 资源整体丢失，SQL 只是其中一个

**验证方法**：用 `nm -a` 取最终可执行文件中定义的 `qInitResources_*` 集合，再与 `.build/krita-ios` 下每个 `*.a` 用 `nm -gU` 定义的集合求差。

**结果**：最终可执行文件共定义 67 个 `qInitResources_*`，恰好等于 `krita/CMakeLists.txt:170-193` 的 `krita_QRCS`（直接编入可执行目标的那一组）加 Qt/KF/QML 自身的资源。**凡是在静态库里的 qrc，一个都没进来**。确认丢失清单（库 → 丢失的资源集）：

| 静态库 | 丢失的 qrc 资源 |
|---|---|
| `libkritaresources.a` | `sql`（`:/create_version_information.sql` 等全部 SQL） |
| `libkritadefaulttools.a` | `defaulttools` |
| `libkrita_flaketools.a` | `defaulttools` |
| `libkrita_karbontools.a` | `karbontools` |
| `libkrita_shape_paths.a` | `pathshapes` |
| `libkrita_tool_svgtext.a` | `svgtexttool` |
| `libkritaselectiontools.a` | `selectiontools` |
| `libkritatoolcrop.a` | `toolcrop` |
| `libkritatoolpolygon.a` | `tool_polygon` |
| `libkritatoolpolyline.a` | `polyline` |
| `libkritatooltransform.a` | `tool_transform` |
| `libkritatextproperties.a` | `textproperties` |
| `libkritaqmlwidgets.a` | `kisquickwidgets` |
| `libkritawidgetutils.a` | `kxmlgui` |

**机制（已在生成本身上确认）**

- `.build/krita-ios/libs/resources/qrc_sql.cpp` 尾部只靠匿名命名空间里的静态对象注册资源：
  ```cpp
  namespace { struct initializer { initializer() { qInitResources_sql(); } ... } dummy; }
  ```
- `libs/resources/CMakeLists.txt:62` 用 `qt_add_resources(kritaresources_LIB_SRCS sql.qrc)` 把生成文件编进 `kritaresources` 库；`kis_add_library` 在静态模式下产出 `.a`。
- 链接命令行里 `lib/libkritaresources.a` 是**普通列举**，`build.ninja` 中不存在 `WHOLE_ARCHIVE`、`force_load` 或 `-all_load`。
- 归档成员只有在解析未定义符号时才会被拉入；`qrc_sql.cpp.o` 不被任何人引用，因此其静态构造从不执行，资源也就从不注册。

**为什么这个范围比文档描述更重要**

- `device-startup-issues-2026-09-23.md` 把它写成"SQL 内嵌资源对象没有进入最终可执行文件"，容易导致只针对 `sql.qrc` 打补丁；那样工具图标、工具选项 UI、kxmlgui 资源仍会缺失，之后会以"另一批资源找不到"的形式再次暴露。
- 修复方向不能简单用 whole-archive：`defaulttoolsv` 这个同名资源符号**同时定义在 `libkritadefaulttools.a` 和 `libkrita_flaketools.a`**，强制全量加载会引入重复符号冲突（这也正是文档中"同名工厂需区分命名"那类问题的同一来源）。
- 更稳妥的方向是把相关 `.qrc` 加入 `krita_QRCS` 一类直接编入可执行目标的列表，或对静态构建显式 `Q_INIT_RESOURCE(...)`；无论采用哪种，都应同时补上"最终可执行文件必须包含 `:/create_version_information.sql`"这一检查。

### P1 —— 证据与校验链路

#### RV-03　真机截图证据不在文档所写路径（唯一直接证据缺失）

`docs/ios/device-startup-issues-2026-09-23.md:13` 引用：

```
<local-attachments>/IMG_0150.PNG
<local-attachments>/IMG_0151.PNG
<local-attachments>/IMG_0152.PNG
```

实测：这三个文件都不存在；`~/Downloads` 中只有 `IMG_0153.jpg`（20,456 B）与 `IMG_0154.jpg`（8,574 B）；在用户主目录 3 层内也搜索不到 `IMG_0150`–`IMG_0152`。

**影响**：整份启动阻塞记录（"显示启动画面 → 资源数据库初始化失败 → Krita will quit now"）目前只能靠文档内的文字引用成立，没有可复查的原始证据。建议把截图复制到 `docs/ios/evidence/`（或直接引用现存文件），并避免引用工作区外的绝对路径。

#### RV-04　`export-krita-patch.py` 会把补丁覆盖成 0 字节且返回成功

`packaging/ios/export-krita-patch.py:8-16`：

- 无内容检查、无 HEAD 检查、无临时文件 + rename。
- 在干净树上（新克隆、已 revert、或 checkout 到了错误提交）`git diff HEAD` 为空且无未跟踪文件，`out.write_bytes(b"")` 会把 75 KB 的补丁**替换成 0 字节**，脚本仍打印路径并以 0 退出。
- 写入中途被中断会留下截断的补丁。

**影响**：`patches/ios/krita-ipados.patch` 是本地全部移植改动唯一的载体（仓库无提交、上游目录不在 Git 管理内）。这条脚本一旦在错误状态下运行，会静默销毁唯一的可恢复副本。

#### RV-05　`verify-krita-app.py` 全部使用裸 `assert`

`packaging/ios/verify-krita-app.py` 的 10 处检查（第 16、17、19、21、25、27、29、32、33、34 行）全部是裸 `assert`。在 `python3 -O` 或 `PYTHONOPTIMIZE=1` 下这些语句被整体编译掉，脚本仍会打印 `PASS: ...`。

**影响**：它是打包流程中**唯一的应用级门禁**（`package-krita.sh:16`）。对比之下 `verify-target-libs.py:21` 与 `:14` 正确使用了 `raise SystemExit`。

**补充**：该脚本的检查范围只有架构、平台、动态依赖、4 个 bundle 存在性与 CRC、包内无 `.a`、无符号链接。**完全不检查 qrc 内嵌资源**——这正是 RV-02 逃过打包检查的原因。

#### RV-06　IPA 本身从未被脚本校验，而文档声称校验通过

对 `packaging/ios/` 全文检索 `codesign` / `testzip` / `unzip -t` / `CRC` / `plutil`，只有两处命中：

- `package-krita.sh:13`：`plutil -lint "$app/Info.plist"`（校验的是 **app 内的 plist**，不是 IPA）。
- `verify-krita-app.py:32`：对 4 个 `.bundle` 做 `testzip()`。

也就是说：

- `package-krita.sh:17-27` 写完 IPA 就结束，**没有任何脚本重新打开 IPA 做 ZIP CRC 或 plist 校验**；IPA 内 `Payload/krita.app/Info.plist` 是否与源一致也未复验。
- 全流程**没有任何 codesign 检查**（本次是手工执行的）。
- 但 `README.md:5` 写"IPA 完整性检查均通过"，`phase-2.md:74` 写"IPA 的结构、CRC 与 plist 检查通过"、"codesign 确认应用未签名"。这些结论是人工执行的，**无法从现有入口复现**，也没有记录命令。
- `verify-krita-app.py:35-36` 会把 `PASS` 与 `device launch: NOT VERIFIED` 打印在同一行输出里，容易被后续引用时截断成"校验通过"。

**本次手工复核结果**：IPA `unzip -t` 通过；应用未签名；仅依赖系统库。即当前产物没问题，问题在于**该结论没有自动化保障**。

#### RV-07　依赖 pin 的保护实际无效，改 pin 会静默构建旧版本

`packaging/ios/build-krita-deps.sh:37-43`：

```bash
if ! git -C "$src" rev-parse --verify HEAD >/dev/null 2>&1; then
 git -C "$src" fetch --depth 1 origin "$revision"
 git -C "$src" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$src" rev-parse HEAD)" != "$(git -C "$src" rev-parse --verify "${revision}^{commit}" 2>/dev/null || git -C "$src" rev-parse "FETCH_HEAD^{commit}")" ]]; then
 echo "Unexpected source revision for $name; not changing the existing checkout" >&2; exit 1
fi
```

实测：`.deps/src/freetype` 中 `git rev-parse --verify "VER-2-14-3^{commit}"` **失败**（报"需要一个单独的版本"），exiv2 的 `v0.28.8` 同样失败；只有全 SHA 的 pin（gsl、lager）和带 tag ref 的 KDE 包能真正解析。

**后果链条**：

1. 首次 setup 时 `HEAD` 就是 `FETCH_HEAD`，第 41 行必然相等，检查永远通过。
2. 之后每次重跑时，pin 解析失败会回退到**上一次遗留的 `FETCH_HEAD`**（实测四个 checkout 都留有 `FETCH_HEAD`），而 `HEAD` 通常就等于它。
3. 因此若把 `revision` 改成新版本再重跑，第 37 行因 `HEAD` 已存在而跳过 fetch，第 41 行回退比较旧 `FETCH_HEAD` 并"通过"，**脚本会继续构建旧版本而不报错**。

这与 `README.md:33`／`phase-2.md:16` 强调"固定提交"的说法不符。建议改为 `git fetch --depth 1 origin "refs/tags/$revision"` 之类的可直接解析引用，或与 `logs/deps-*-revision.txt` 中记录的实际 revision 比对。

### P2 —— 文档一致性与环境风险

#### RV-08　状态陈述过时或互相矛盾

| # | 位置 | 文档说法 | 实际情况 |
|---|---|---|---|
| a | `README.md:5` | "完整应用尚待真机启动与绘画验证" | 与同文件第 3 行、以及 `device-startup-issues` 全文冲突：真机已启动、已在资源库初始化处失败 |
| b | `phase-2.md:1` | 标题"完整 Krita 应用已构建，**待真机启动**" | 同上；文档尾部 70-78 行已记录真机结果 |
| c | `device-checklist.md:1,6-20` | 标题"阶段 1 真机验收（**全部待执行**）"，全部行"未验证" | `README.md:14`、`project-overview.md:44`、`phase-0-1.md:66-68` 均记录探针已在真机运行并被用户确认 |
| d | `krita-app-validation.txt:11` | "Personal signing / device launch / drawing: NOT VERIFIED" | 真机启动已尝试并失败；`project-overview.md:120` 有说明，但 `README.md:9` 仍把它作为当期"产物检查结果"链接且无提示 |
| e | `dependencies.md:10,15` | "本轮只安装 qtbase…SQLite 资源数据库尚未验收"、"尚未运行完整 Krita iOS 配置"、"当前真正完成的是探针构建" | 这是阶段 2 之前的快照，与 `phase-2.md:70-78`、`project-overview.md:7` 直接冲突，却仍被 `README.md:28` 与 `project-overview.md:136` 无标注地链接 |

#### RV-09　小的数据/引用不一致

- `phase-2.md:13` 写 "libunibreak 7.0"；`.deps/ios/lib/pkgconfig/libunibreak.pc` 与源码 `project()` 均为 **5.0**（头文件 `UNIBREAK_VERSION` 是 `0x0700`）。数字无法对齐，需确认是写法问题还是实际装了 5.0。
- `phase-2.md:68` 的"未构建的可选库"清单缺少 KSeExpr，而 `project-overview.md:91` 包含它。
- `dependency-declarations.md` 的行号普遍指向声明**前一行**（例如 `FindHarfBuzz.cmake:67`→实际 68、`FindQUAZIP.cmake:9`→实际 10、`CheckLibTIFFPSDSupport.cmake:53`→实际 54）。原因在 `packaging/ios/inventory-deps.py:12` 的正则 `^\s*` 会跨行匹配到前一个换行。按固定提交重新生成后内容与文件完全一致（105 行，零差异），所以这是**引用偏移**而非内容过期。
- `docs/ios/krita-app-validation.txt` 与 `logs/krita-app-validation.txt` 同名但内容不同（前者是人工汇总，后者是 `verify-krita-app.py` 的原始输出），引用时容易混淆。
- 三个脚本会直接覆盖仓库内文件而无需确认：`inventory-deps.py` → `docs/ios/dependency-declarations.md`、`export-krita-patch.py` → `patches/ios/krita-ipados.patch`、`verify-krita-app.py` 经 `package-krita.sh` → `logs/krita-app-validation.txt`。文档中引用这些文件时未说明它们会被脚本重写。

#### RV-10　README 的复现链不完整

`README.md:10` 只给出：

```
configure-krita.sh → build-krita-app.sh → package-krita.sh
```

完整的依赖链（`fetch-source.sh`、`apply-krita-patch.sh`、`build-deps.sh`、`provision-krita-tools.sh`、`build-krita-deps.sh` 各包、`build-gettext.sh`、`fetch-boost.sh`、`build-fontconfig.sh`、`build-fribidi.sh`）只存在于 `phase-2.md:20-46`。在新机器上只按 README 操作必然失败。另：`packaging/ios/*.py` 都带 `#!/usr/bin/env python3`，但文件权限是 644，不能直接执行。

#### RV-11　磁盘余量偏低

`df` 显示数据卷 460 GiB / 已用 407 GiB / **可用 32 GiB（93%）**。工作区自身占用约 30 GB：

```
.build   14G      .qt      13G      .deps   2.2G
upstream 794M     logs     4.0M     docs    108K     packaging 156K
```

其中 `.deps/downloads` 138M、`.deps/src` 1.9G、`.deps/ios` 94M、`.deps/host` 4.9M。RV-01 要求的 Release 重建（新的构建目录 + 新的 qt 链接）在 32 GB 余量下存在失败风险，需要先清理或迁移。

#### RV-12　外层仓库没有任何提交

`git log` 报 "当前分支 'master' 尚无任何提交"，`git status` 有 88 个未跟踪条目（`README.md`、`docs/`、`packaging/`、`patches/`、`.gitignore` 等全部在内）。这符合"按用户要求本轮不提交 Git"的约定，但从备份与历史角度看：脚本、文档、补丁**只有工作区这一份**，没有版本历史可回溯。此条仅作风险登记，不代表需要立即改变约定。

### P3 —— 其他脚本健壮性问题（逐条已核对源码）

| # | 位置 | 问题 | 影响 |
|---|---|---|---|
| a | `build-fontconfig.sh:48` vs `49-51` | `quote-pkgconfig-paths.py` 在 `meson install` **之前**执行 | 单独运行 fontconfig 时，新安装的 `fontconfig.pc` 未被加引号；目前只因后续 `build-fribidi.sh:18` 会重新处理同一前缀才没暴露 |
| b | `build-fontconfig.sh:7-11`、`build-fribidi.sh:6-10` | 未 `mkdir -p .deps/downloads`/`.deps/src`（对比 `fetch-boost.sh:5`、`build-gettext.sh:19` 有做） | 全新机器上 `curl -o` 会直接失败 |
| c | `build-fontconfig.sh:8`、`build-fribidi.sh:7` | 下载非原子（无 `.partial` + `mv`，对比 `fetch-boost.sh:7-8`、`build-gettext.sh:21-22` 有做） | 中断的下载会污染 `[[ -f "$archive" ]]` 缓存，之后哈希校验才失败，需要手工删除 |
| d | `build-gettext.sh:37`、`fetch-boost.sh:13` | 只把 sha256 **写入日志**，从不比对 | "记录"容易被误读为"校验"；对比 fontconfig/fribidi 至少做了 `shasum -c` |
| e | `build-device.sh:3` | 只要 `KritaIOSProbe.xcodeproj` 存在就跳过 `configure.sh` | 修改 `KRITA_IOS_BUNDLE_ID` / `KRITA_IOS_MIN_VERSION` 后重跑会被静默忽略（Team ID 因在构建期传入仍生效）；`build.md:29-30` 只能靠"先手动跑 configure"绕开 |
| f | `quote-pkgconfig-paths.py:6` | 无 `sys.argv` 长度检查、无目录存在性检查；目录不存在时 `glob` 返回空 → 静默无操作并返回 0 | 使 (a) 类问题长期不可见；无参数调用会抛 `IndexError` |
| g | `inventory-deps.py:13-14` | 若 `find(')')` 返回 -1，切片 `[start:0]` 得到空串 | 畸形的 `find_package(` 行会静默产出空表格单元格 |
| h | `common.sh:2-9` | 所有 `set -euo pipefail` 都来自 source；各入口脚本自身没有设置 | `common.sh` 缺失/不可读时，调用方在零错误处理下继续运行 |
| i | `build-krita-deps.sh:33-36` | 对已存在的**非 Git** 目录直接 `git init` 再 `checkout --detach` | 预置的发布包目录会被当作仓库操作；`fetch-source.sh:6` 对同种情况只报 "Existing checkout differs"（安全但提示误导） |

**规则符合性检查（通过）**：脚本中没有任何硬编码 Team ID 或个人签名身份（`KRITA_IOS_TEAM_ID` 默认为空）、没有任何 `git add/commit/push/reset/clean`、没有任何 `/Users/...` 绝对路径（唯一绝对字面量是 `build-gettext.sh:13` 的 `/private/tmp`）；也没有 `rm -rf`、`|| true` 或未检查退出码的写法。

---

## 4. 建议的处理顺序（尚未执行）

1. **先修校验链路，再修产品**：RV-04（补丁导出保护）、RV-05（`assert` → `SystemExit`）、RV-06（补一条真正打开 IPA 的校验）——否则修完 SQL 依然没有可信门禁。
2. **RV-02 用通用方案修**，不要只针对 `sql.qrc`；同时给 `verify-krita-app.py` 增加"最终可执行文件包含 `:/create_version_information.sql`"以及"丢失的 qrc 资源集为空"的检查。注意 `defaulttoolsv` 重名，避免 whole-archive。
3. **RV-01 的 Release 重建**放在真机主窗口跑通之后；届时先处理 RV-11 的磁盘余量。
4. **RV-03 补齐证据文件**，RV-08/RV-09 统一文档状态（或为早期快照加"历史文档"标注）。
5. RV-07、RV-10 及 P3 各项属于后续健壮性改进，可与其他修复合并。

## 5. 复核命令（可复现）

```bash
# 基线、改动与补丁一致性
git -C upstream/krita rev-parse HEAD
git -C upstream/krita status --short
# 重新生成 diff（含未跟踪新文件）并与 patches/ios/krita-ipados.patch 逐字节比较
# 见 packaging/ios/export-krita-patch.py 的内容，改用内存比较即可

# 静态归档：遍历 docs/ios/krita-core-libraries.txt 的 194 个名称
# 对每个归档执行 xcrun lipo -archs <lib> 与 xcrun otool -l <lib> | grep platform
# 本次结果：194/194 为 arm64 + platform 2

# SQL 资源是否进入最终程序
nm -gU .build/krita-ios/lib/libkritaresources.a | grep -i qInitResources_sql
nm -a  .build/krita-ios-install/krita.app/krita | grep -c qInitResources_sql        # 期望 0
strings -a .build/krita-ios-install/krita.app/krita | grep -c create_version_information  # 期望 0

# 丢失的 qrc 资源集（RV-02 的清单来源）
nm -a .build/krita-ios-install/krita.app/krita | grep -v OSO \
  | grep -o 'qInitResources_[A-Za-z0-9_]*' | sort -u
find .build/krita-ios -name '*.a' -exec sh -c \
  'nm -gU "$1" 2>/dev/null | grep -q qInitResources && echo "== $1" && nm -gU "$1" | grep qInitResources' _ {} \;

# 构建类型与优化级别
grep CMAKE_BUILD_TYPE .build/krita-ios/CMakeCache.txt
grep -o '\-O[0-3s]' .build/krita-ios/build.ninja | sort | uniq -c     # 本次输出为空
grep -c DNDEBUG .build/krita-ios/build.ninja                          # 本次为 0

# 产物与 IPA
shasum -a 256 .build/Krita-iPadOS-unsigned.ipa
unzip -t .build/Krita-iPadOS-unsigned.ipa
for b in .build/krita-ios-install/krita.app/share/krita/bundles/*.bundle; do unzip -t "$b"; done
codesign -dv .build/krita-ios-install/krita.app/krita
otool -L .build/krita-ios-install/krita.app/krita

# 环境
xcodebuild -version; cmake --version; sw_vers; df -h .
```

## 6. 状态与边界

- 本文只做记录，**不代表任何问题已修复**。上一轮用户的要求是"先确认问题，不解决"，本轮延续该要求。
- 本文不改变 `README.md`、`project-overview.md` 或任何既有文档；如需把本文纳入文档导航，请另行确认。
- 未验证的部分（真机主窗口、画布、Pencil、Files、保存恢复、Release 性能）不在本文结论范围内，仍以 `project-overview.md` 的阶段表为准。
