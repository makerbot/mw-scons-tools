
cmake_minimum_required(VERSION 3.1.0)

project(mw-scons-tools NONE)

# import our standard tools
find_package(MBCMakeTools REQUIRED)

configure_file(mb_install.py.in mb_install.py @ONLY)

install(
    FILES
        bundle.py
        mb_sconstruct.py
        vcxproj.py
        hook_settings.py
        version.py
        doxygen.py
        __init__.py
        mustache.py
        scons_condensed_readme.md
        mb_test.py
        log.py
        common.py
        ${PROJECT_BINARY_DIR}/mb_install.py
        rc.py
        cxx_gen.py
        options.py
        addDependentLibsToBundle.py
        qrc.py
    DESTINATION "scons")

install(
    FILES
        templates/version.rc
        templates/vcxproj.xml
        templates/project_configuration.xml
        templates/configuration_group.xml
        templates/version_info.h
    DESTINATION "scons/templates")

install(
    FILES
        qt5/__init__.py
    DESTINATION "scons/qt5")
