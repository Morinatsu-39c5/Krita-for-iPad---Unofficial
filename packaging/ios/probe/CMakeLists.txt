cmake_minimum_required(VERSION 3.24)
project(KritaIOSProbe VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Qt6 6.10 REQUIRED COMPONENTS Core Gui Widgets OpenGLWidgets)
qt_standard_project_setup()
qt_add_executable(KritaIOSProbe MANUAL_FINALIZATION main.cpp)
target_link_libraries(KritaIOSProbe PRIVATE Qt6::Widgets Qt6::OpenGLWidgets)
if(IOS)
    enable_language(OBJCXX)
    target_sources(KritaIOSProbe PRIVATE FilesExport.mm Assets.xcassets)
    set_source_files_properties(Assets.xcassets PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
    set_target_properties(KritaIOSProbe PROPERTIES XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_APPICON_NAME AppIcon)
    set_source_files_properties(FilesExport.mm PROPERTIES COMPILE_OPTIONS "-fobjc-arc")
    target_link_libraries(KritaIOSProbe PRIVATE "-framework UIKit")
    set(KRITA_IOS_BUNDLE_ID "org.example.krita.probe" CACHE STRING "Unique signing bundle identifier")
    set(KRITA_IOS_TEAM_ID "" CACHE STRING "Apple development team")
    if(NOT CMAKE_OSX_ARCHITECTURES STREQUAL "arm64")
        message(FATAL_ERROR "The device probe requires arm64")
    endif()
    if(CMAKE_OSX_DEPLOYMENT_TARGET VERSION_LESS 17.0)
        message(FATAL_ERROR "Qt 6.10 probe requires iPadOS 17 or newer")
    endif()
    set_target_properties(KritaIOSProbe PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in"
        MACOSX_BUNDLE_GUI_IDENTIFIER "${KRITA_IOS_BUNDLE_ID}"
        XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "${KRITA_IOS_BUNDLE_ID}"
        XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "2"
        XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Automatic"
        XCODE_ATTRIBUTE_ENABLE_BITCODE "NO"
        XCODE_ATTRIBUTE_GENERATE_INFOPLIST_FILE "NO")
    if(KRITA_IOS_TEAM_ID)
        set_target_properties(KritaIOSProbe PROPERTIES XCODE_ATTRIBUTE_DEVELOPMENT_TEAM "${KRITA_IOS_TEAM_ID}")
    endif()
elseif(APPLE AND NOT IOS)
    set_target_properties(KritaIOSProbe PROPERTIES MACOSX_BUNDLE TRUE)
endif()
# Qt's finalizer imports the static iOS platform and image format plugins.
qt_finalize_executable(KritaIOSProbe)
