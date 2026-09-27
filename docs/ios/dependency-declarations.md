# Krita CMake dependency declarations

Source: `3a9b5ef03f8312b6f630fc5d475e1692598e8719`.

Static inventory, including conditional/optional/test/vendor declarations. Versions and variables remain literal; this is not a successful iOS resolution. Classification is in dependencies.md.

| Source | Declaration |
| --- | --- |
| `3rdparty_vendor/raqm/CMakeLists.txt:28` | `find_package(FriBidi 1.0.6 REQUIRED)` |
| `CMakeLists.txt:446` | `find_package(Python 3.8 COMPONENTS Development Interpreter)` |
| `CMakeLists.txt:448` | `find_package(PythonLibrary 3.8)` |
| `CMakeLists.txt:457` | `find_package(PythonLibrary 3.8)` |
| `CMakeLists.txt:468` | `find_package(ECM 6.0 REQUIRED CONFIG)` |
| `CMakeLists.txt:471` | `find_package(ECM 5.91 REQUIRED CONFIG)` |
| `CMakeLists.txt:548` | `find_package(KF${KF_MAJOR} ${MIN_FRAMEWORKS_VERSION} REQUIRED COMPONENTS Config WidgetsAddons Completion CoreAddons GuiAddons I18n ItemViews )` |
| `CMakeLists.txt:557` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} REQUIRED COMPONENTS Core Gui Widgets Xml Network PrintSupport Svg Test Concurrent Sql )` |
| `CMakeLists.txt:574` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} REQUIRED COMPONENTS AndroidExtras )` |
| `CMakeLists.txt:582` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} REQUIRED COMPONENTS Core5Compat OpenGL OpenGLWidgets SvgWidgets )` |
| `CMakeLists.txt:589` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} OPTIONAL_COMPONENTS WaylandClient )` |
| `CMakeLists.txt:594` | `find_package(KF6 ${MIN_FRAMEWORKS_VERSION} REQUIRED COMPONENTS ColorScheme )` |
| `CMakeLists.txt:602` | `find_package(Qt6GuiPrivate ${REQUIRED_QT_VERSION} REQUIRED NO_MODULE)` |
| `CMakeLists.txt:606` | `find_package(Qt6CorePrivate ${REQUIRED_QT_VERSION} REQUIRED NO_MODULE)` |
| `CMakeLists.txt:623` | `find_package(Qt6WaylandClientPrivate ${REQUIRED_QT_VERSION} REQUIRED NO_MODULE)` |
| `CMakeLists.txt:886` | `find_package(Qt${QT_MAJOR_VERSION}Quick ${MIN_QT_VERSION})` |
| `CMakeLists.txt:895` | `find_package(Qt${QT_MAJOR_VERSION}QuickWidgets ${MIN_QT_VERSION})` |
| `CMakeLists.txt:907` | `find_package(Qt${QT_MAJOR_VERSION}QuickControls2 ${MIN_QT_VERSION})` |
| `CMakeLists.txt:920` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} REQUIRED X11Extras)` |
| `CMakeLists.txt:922` | `find_package(Qt${QT_MAJOR_VERSION}DBus ${MIN_QT_VERSION})` |
| `CMakeLists.txt:930` | `find_package(KF${KF_MAJOR}Crash ${MIN_FRAMEWORKS_VERSION})` |
| `CMakeLists.txt:938` | `find_package(X11 REQUIRED COMPONENTS Xinput)` |
| `CMakeLists.txt:1155` | `find_package(unwindstack REQUIRED)` |
| `CMakeLists.txt:1157` | `find_package(PNG REQUIRED "1.6.0")` |
| `CMakeLists.txt:1170` | `find_package(Boost 1.69 REQUIRED)` |
| `CMakeLists.txt:1190` | `find_package(Immer REQUIRED)` |
| `CMakeLists.txt:1192` | `find_package(Zug REQUIRED)` |
| `CMakeLists.txt:1193` | `find_package(Lager REQUIRED)` |
| `CMakeLists.txt:1198` | `find_package(GSL)` |
| `CMakeLists.txt:1211` | `find_package(WebP 1.2.0 COMPONENTS demux mux)` |
| `CMakeLists.txt:1224` | `find_package(KSeExpr 4.0.0.0)` |
| `CMakeLists.txt:1226` | `find_package(KSeExpr 6.0.0.0)` |
| `CMakeLists.txt:1235` | `find_package(ZLIB REQUIRED)` |
| `CMakeLists.txt:1243` | `find_package(OpenEXR)` |
| `CMakeLists.txt:1249` | `find_package(TIFF)` |
| `CMakeLists.txt:1258` | `find_package(JPEG)` |
| `CMakeLists.txt:1268` | `find_package(libjpeg-turbo 2.1.3 COMPONENTS turbojpeg)` |
| `CMakeLists.txt:1281` | `find_package(GIF)` |
| `CMakeLists.txt:1288` | `find_package(HEIF "1.11.0")` |
| `CMakeLists.txt:1295` | `find_package(OpenJPEG "2.3.0")` |
| `CMakeLists.txt:1302` | `find_package(JPEGXL 0.7.0)` |
| `CMakeLists.txt:1309` | `find_package(FFTW3)` |
| `CMakeLists.txt:1321` | `find_package(OpenColorIO 2.0.0)` |
| `CMakeLists.txt:1337` | `find_package(SIP "4.19.13")` |
| `CMakeLists.txt:1347` | `find_package(PyQt5 "5.6.0")` |
| `CMakeLists.txt:1361` | `find_package(PyQt6 "6.7.0")` |
| `CMakeLists.txt:1374` | `find_package(Mlt7)` |
| `CMakeLists.txt:1380` | `find_package(SDL2 REQUIRED)` |
| `CMakeLists.txt:1387` | `find_package(LibMyPaint 1.4.0)` |
| `CMakeLists.txt:1411` | `find_package(Eigen3 5 NO_MODULE)` |
| `CMakeLists.txt:1413` | `find_package(Eigen3 3.3 REQUIRED NO_MODULE)` |
| `CMakeLists.txt:1423` | `find_package(LibExiv2 0.16 REQUIRED)` |
| `CMakeLists.txt:1428` | `find_package(LCMS2 2.4 REQUIRED)` |
| `CMakeLists.txt:1466` | `find_package(xsimd ${xsimd_version})` |
| `CMakeLists.txt:1514` | `find_package(Poppler COMPONENTS Qt${QT_MAJOR_VERSION})` |
| `CMakeLists.txt:1525` | `find_package(PkgConfig REQUIRED)` |
| `CMakeLists.txt:1563` | `find_package(QUAZIP 0.6)` |
| `CMakeLists.txt:1575` | `find_package(KDcrawQt6 5.0.0)` |
| `CMakeLists.txt:1583` | `find_package(KF5KDcraw 5.0.0)` |
| `CMakeLists.txt:1595` | `find_package(Freetype 2.11.0 REQUIRED)` |
| `CMakeLists.txt:1607` | `find_package(HarfBuzz 2.7.4 REQUIRED)` |
| `CMakeLists.txt:1609` | `find_package(HarfBuzz 4.0 REQUIRED)` |
| `CMakeLists.txt:1626` | `find_package(Fontconfig 2.13.1 REQUIRED)` |
| `CMakeLists.txt:1635` | `find_package(libunibreak 5.0 REQUIRED)` |
| `cmake/modules/CheckLibTIFFPSDSupport.cmake:53` | `find_package(TIFF REQUIRED QUIET)` |
| `cmake/modules/FindFFTW3.cmake:76` | `find_package(FFTW3 QUIET NO_MODULE HINTS ${PKG_FFTW_CONFIG_DIR} /usr/lib/cmake/fftw3 /usr/local/lib/cmake/fftw3 )` |
| `cmake/modules/FindFFTW3.cmake:89` | `find_package(FFTW3f QUIET NO_MODULE HINTS ${PKG_FFTW_CONFIG_DIR} /usr/lib/cmake/fftw3 /usr/local/lib/cmake/fftw3 )` |
| `cmake/modules/FindFFTW3.cmake:93` | `find_package(FFTW3l QUIET NO_MODULE HINTS ${PKG_FFTW_CONFIG_DIR} /usr/lib/cmake/fftw3 /usr/local/lib/cmake/fftw3 )` |
| `cmake/modules/FindFFTW3.cmake:98` | `find_package(FFTW3q QUIET NO_MODULE HINTS ${PKG_FFTW_CONFIG_DIR} /usr/lib/cmake/fftw3 /usr/local/lib/cmake/fftw3 )` |
| `cmake/modules/FindFFTW3.cmake:174` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindFFmpeg.cmake:63` | `find_package(PkgConfig)` |
| `cmake/modules/FindFriBidi.cmake:37` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindGSL.cmake:84` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindHEIF.cmake:43` | `find_package(libheif QUIET NO_MODULE HINTS ${HEIF_PKGCONF_CONFIG_DIR} /usr/lib/cmake/libheif /usr/local/lib/cmake/libheif )` |
| `cmake/modules/FindHEIF.cmake:80` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindHarfBuzz.cmake:67` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindJPEGXL.cmake:54` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindLCMS2.cmake:18` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindLibExiv2.cmake:44` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindLibMyPaint.cmake:42` | `find_package(libmypaint QUIET NO_MODULE HINTS ${MYPAINT_PKGCONF_CONFIG_DIR} /usr/lib/cmake/libmypaint /usr/local/lib/cmake/libmypaint )` |
| `cmake/modules/FindLibMyPaint.cmake:72` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindOpenEXR.cmake:54` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindOpenEXR.cmake:65` | `find_package(OpenEXR QUIET NO_MODULE HINTS ${PC_OpenEXR_CONFIG_DIR} /usr/lib/cmake/OpenEXR /usr/local/lib/cmake/OpenEXR )` |
| `cmake/modules/FindOpenJPEG.cmake:48` | `find_package(OPENJPEG QUIET NO_MODULE NAMES OpenJPEG)` |
| `cmake/modules/FindOpenJPEG.cmake:134` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindPythonLibrary.cmake:37` | `find_package(Python 3.8 REQUIRED COMPONENTS Development Interpreter)` |
| `cmake/modules/FindPythonLibrary.cmake:39` | `find_package(Python 3.8 REQUIRED COMPONENTS Interpreter OPTIONAL_COMPONENTS Development)` |
| `cmake/modules/FindQUAZIP.cmake:9` | `find_package(QuaZip-Qt${QT_MAJOR_VERSION} QUIET)` |
| `cmake/modules/FindQUAZIP.cmake:35` | `FIND_PACKAGE(PkgConfig)` |
| `cmake/modules/FindRaqm.cmake:36` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/FindWebP.cmake:77` | `find_package(WebP QUIET NO_MODULE HINTS ${PC_WEBP_CONFIG_DIR} /usr/share/WebP/cmake /usr/local/share/WebP/cmake )` |
| `cmake/modules/FindWebP.cmake:123` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/Findlibjpeg-turbo.cmake:50` | `find_package(libjpeg-turbo QUIET NO_MODULE)` |
| `cmake/modules/Findlibjpeg-turbo.cmake:88` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/Findlibunibreak.cmake:36` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/Findxsimd.cmake:5` | `find_package(PkgConfig QUIET)` |
| `cmake/modules/Findxsimd.cmake:8` | `find_package(xsimd QUIET NO_MODULE HINTS ${PC_xsimd_CONFIG_DIR} /usr/lib/cmake/xsimd /usr/local/lib/cmake/xsimd )` |
| `cmake/modules/GetGitRevisionDescription.cmake:89` | `find_package(Git QUIET)` |
| `cmake/modules/GetGitRevisionDescription.cmake:133` | `find_package(Git QUIET)` |
| `cmake/modules/GetGitRevisionDescription.cmake:160` | `find_package(Git QUIET)` |
| `cmake/modules/MacroJPEG.cmake:40` | `find_package(JPEG REQUIRED)` |
| `cmake/modules/avcodecs/FindFLAC.cmake:16` | `find_package (Ogg QUIET)` |
| `cmake/modules/avcodecs/FindFLAC.cmake:18` | `find_package (PkgConfig QUIET)` |
| `plugins/dockers/recorder/CMakeLists.txt:3` | `find_package(Threads REQUIRED)` |
| `plugins/qt/designer/CMakeLists.txt:1` | `find_package(Qt${QT_MAJOR_VERSION} ${MIN_QT_VERSION} REQUIRED COMPONENTS Designer )` |
