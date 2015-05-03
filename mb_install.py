import os
import platform
import re
import shutil
import SCons

'''
Some conventions to keep this sane:
  * function definitions are in lowercase_with_underscores
  * if the function is exported by the tool, it starts with mb_
  * functions/builders are exported in camelcase, including the initial MB
  * functions are added in the same order as they appear in this file
Feel free to change the conventions if you think they're wrong,
just make sure to update everything to match those conventions
'''

symlink_env_name = 'MB_MAC_FRAMEWORK_HEADER_SYMLINK_DONE'

def recursive_install(env, dest, src):
    if not hasattr(src, '__iter__'):
        srcs = [src]
    else:
        srcs = src

    installs = []

    for source in srcs:
        src_str = str(source)
        if not os.path.isdir(src_str):
            inst = env.Install(dest, source)
            if isinstance(inst, list):
                installs.extend(inst)
            else:
                installs.append(inst)
        else:
            base = os.path.join(dest, os.path.basename(src_str))
            for curpath, dirnames, filenames in os.walk(str(source)):
                relative = os.path.relpath(curpath, source)
                installs.append(env.Install(os.path.join(base, relative),
                                            map(lambda f: os.path.join(curpath, f),
                                                filenames)))

    return installs

def mb_install_lib(env, source, name, dest=''):
    targets = []
    if env.MBIsMac():
        framework = os.path.join(env['MB_FRAMEWORK_DIR'], name + '.framework')
        version_dir = os.path.join('Versions', env['MB_VERSION'])
        libinst = env.InstallAs(os.path.join(framework, version_dir, name),
                                source)
        targets.append(libinst)

        #make relative symlinks between Current and the new version
        current_dir = 'Current'
        current_link = env.Command(os.path.join(framework, 'Versions',
                                                current_dir),
                                   libinst,
                                   'cd ' + os.path.join(framework, 'Versions')
                                   + ' && ln -sf ' +
                                   env['MB_VERSION'] + ' ' + current_dir)
        targets.append(current_link)

        #make a relative symlink for the current lib
        targets.append(env.Command(os.path.join(framework, name),
                                   current_link, 'cd ' + framework +
                                   ' && ln -sf ' +
                                   os.path.join('Versions', current_dir, name)
                                             + ' ' + name))

    else:
        if dest is not None and dest != '':
            targetpath = os.path.join(env['MB_LIB_DIR'], dest)
        else:
            targetpath = env['MB_LIB_DIR']
        targets.append(env.Install(targetpath, source))
        if env.MBIsWindows():
            targets.append(env.Install(env['MB_BIN_DIR'], source))
        elif env.MBIsLinux():
            #make versioned symlinks
            def proclib(source, targets):
                if isinstance(source, list):
                    for elem in source:
                        proclib(elem, targets)
                    return
                elif isinstance(source, SCons.Node.NodeList):
                    for elem in source:
                        proclib(elem, targets)
                    return
                vre = re.compile('(?P<libname>\S+\.so)(?P<libver>(\.\d+)+)')
                sourcename = str(source.abspath).split('/')[-1]
                match = vre.match(sourcename)
                if None is not match and None is not match.group('libver'):
                    libname = match.group('libname')
                    libver = [elem for elem in match.group('libver').split('.')
                            if elem != '']
                    #if we have liblib.so.1.2.3
                    #we will make symbolic links liblib.so.1.2 and liblib.so.1
                    libsource = source.abspath
                    for i in xrange(len(libver) - 1, -1, -1):
                        ver = libver[:i]
                        vername = '.'.join([libname] + ver)
                        createdlink = os.path.join(targetpath, vername)
                        createdlink = os.path.abspath(createdlink)
                        linkpath = os.path.relpath(
                                os.path.join(targetpath, sourcename),
                                os.path.dirname(createdlink))
                        print 'Linking', os.path.basename(createdlink),\
                                'from', linkpath
                        targets.append(env.Command(createdlink, source,
                                'ln -sf -T %s %s' % (linkpath, createdlink)))
                else:
                    pass
            proclib(source, targets)

    env.Append(MB_INSTALL_TARGETS = targets)
    return targets


def mb_install_headers(env, source, name, dest='', make_current_link=False):
    targets = []
    if env.MBIsMac():
        # Name might include subdirectories; if so, split out the
        # top-level directory as the framework name
        #
        # E.g. "conveyor-ui" -> "conveyor-ui"
        #      "conveyor-ui/widgets" -> "conveyor-ui"
        #
        # TODO(nicholasbishop): IMO a more explicit interface that
        # acknowledges better the differences between platforms might
        # be a better idea.
        base_folder = name
        include_subdir = ''
        while os.path.dirname(base_folder) != '':
            include_subdir = os.path.join(os.path.basename(base_folder), include_subdir)
            base_folder = os.path.dirname(base_folder)

        framework_name = base_folder + '.framework'

        framework = os.path.join(env['MB_FRAMEWORK_DIR'], framework_name)
        version_dir = os.path.join('Versions', env['MB_VERSION'])
        include_dir = os.path.join(version_dir, 'Headers', include_subdir)

        headers = recursive_install(env, os.path.join(framework, include_dir), source)
        targets += headers

        #make relative symlinks between Current and the new version
        current_dir = 'Current'

        symlink_key = symlink_env_name + framework_name
        symlink_key = symlink_key.replace('-', '_')
        symlink_key = symlink_key.replace('.', '_')

        if make_current_link and symlink_key not in env:
            current_link = env.Command(
                os.path.join(framework, 'Versions', current_dir),
                headers,
                'cd {base_dir} && ln -sf {from_dir} {to_dir}'.format(
                    base_dir=os.path.join(framework, 'Versions'),
                    from_dir=env['MB_VERSION'],
                    to_dir=current_dir))

            targets.append(current_link)

        #make a relative symlink for the current headers
        toplink = os.path.join(framework, 'Headers')
        target_path = os.path.join(framework, toplink)
        if symlink_key not in env:
            targets.append(env.Command(
                target_path,
                targets, 'cd ' + framework +
                ' && ln -sf ' + os.path.join('Versions',
                                          current_dir,
                                          'Headers')
                + ' ' + toplink))

        env[symlink_key] = True

    else:
        targets = recursive_install(env, os.path.join(env['MB_INCLUDE_DIR'],
                                            os.path.join(dest, name)),
                               source)

    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_bin(env, source):
    target = env.Install(env['MB_BIN_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_resources(env, source, subdir=''):
    targets = recursive_install(env, os.path.join(env['MB_RESOURCE_DIR'], subdir), source)
    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_config(env, source, dest=None):
    if dest is None:
        target = env.Install(env['MB_CONFIG_DIR'], source)
    else:
        target = env.InstallAs(os.path.join(env['MB_CONFIG_DIR'], dest), source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_app(env, source):
    target = env.Install(env['MB_APP_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_egg(env, source):
    target = env.Install(env['MB_EGG_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_system(env, source, dest):
    target = env.InstallAs(os.path.join(env['MB_PREFIX'], dest), source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_create_install_target(env):
    env.Alias('install', env['MB_INSTALL_TARGETS'])

def mb_dist_egg(env, egg_name, source, egg_dependencies = [], python = 'python', version = '2.7'):
    def eggify(base, version):
        return base + '-py' + version + '.egg'

    def installfix(egg):
        if 'MB_MOD_BUILD' in os.environ:
            egg = os.path.join(env['MB_EGG_DIR'], os.path.basename(egg))
        return egg

    deps = [installfix(eggify(e, version)) for e in egg_dependencies]

    environment = env['ENV'].copy()
    environment.update({'PYTHONPATH': deps})
    egg = env.Command(
        eggify(egg_name, version),
        source + [env.File('setup.py')],
        python + ' -c "import setuptools; execfile(\'setup.py\')" bdist_egg',
        ENV = environment)

    env.Depends(egg, deps)

    return egg


def mb_add_lib(env, name, framework=True):
    if env.MBIsMac() and framework and (not env.MBUseDevelLibs()):
        env.Append(FRAMEWORKS = [name])
    else:
        env.Append(LIBS = [name])

def mb_add_include_paths(env, paths):
    env.PrependUnique(CPPPATH=[paths])

def mb_add_standard_compiler_flags(env):
    if not env.MBIsWindows():
        flags = [
            '-pedantic',
            '-Wall',
            '-Wextra',
            '-Wno-variadic-macros',
            '-Wno-long-long',
            '-Wswitch-enum'
        ]

        env.Append(CCFLAGS=flags)

        if env.MBDebugBuild():
            env.Append(CCFLAGS=['-g'])
        else:
            env.Append(CCFLAGS=['-O2'])

def mb_add_devel_lib_path(env, path):
    if env.MBUseDevelLibs():
        if env.MBIsWindows():
            env.MBAddWindowsDevelLibPath(path)
        else:
            env.PrependUnique(LIBPATH = [str(env.Dir(path))])

def mb_add_devel_include_path(env, path):
    if env.MBUseDevelLibs():
        env.PrependUnique(CPPPATH = [str(env.Dir(path))])


def set_install_paths(env):
    prefix = env.MBGetOption('install_prefix')
    if prefix == '':
        # TODO(ted): suffer the results of doing this
        prefix = env.Dir('#/../../Install').path
    env.SetDefault(MB_PREFIX=os.path.abspath(prefix))

    config_prefix = env.MBGetOption('config_prefix')
    if config_prefix != '':
        env.SetDefault(MB_CONFIG_DIR=config_prefix)

    if env.MBIsLinux():
        env.SetDefault(
            MB_INCLUDE_DIR=os.path.join(prefix, 'include'),
            MB_LIB_DIR=os.path.join(prefix, 'lib'),
            MB_BIN_DIR=os.path.join(prefix, 'bin'),
            MB_APP_DIR=os.path.join(prefix, 'bin'),
            MB_RESOURCE_DIR=os.path.join(prefix, 'share', 'makerbot'),
            MB_CONFIG_DIR=os.path.join(prefix, 'etc'),
            MB_EGG_DIR=os.path.join(prefix, 'share', 'makerbot', 'python'))
    elif env.MBIsMac():
        env.SetDefault(
            MB_INCLUDE_DIR=os.path.join(
                prefix, 'Library', 'MakerBot', 'include'),
            MB_LIB_DIR=os.path.join(prefix, 'Library', 'MakerBot', 'lib'),
            MB_BIN_DIR=os.path.join(prefix, 'Library', 'MakerBot'),
            MB_APP_DIR=os.path.join(prefix, 'Applications'),
            MB_RESOURCE_DIR=os.path.join(prefix, 'Library', 'MakerBot'),
            MB_CONFIG_DIR=os.path.join(prefix, 'Library', 'MakerBot'),
            MB_EGG_DIR=os.path.join(prefix, 'Library', 'MakerBot', 'python'))
    elif env.MBIsWindows():
        env.SetDefault(
            MB_INCLUDE_DIR=os.path.join(prefix, 'include'),
            MB_LIB_DIR=os.path.join(prefix, 'lib'),
            MB_BIN_DIR=os.path.join(prefix, 'MakerWare'),
            MB_APP_DIR=os.path.join(prefix, 'MakerWare'),
            MB_RESOURCE_DIR=os.path.join(prefix, 'MakerWare'),
            MB_CONFIG_DIR=os.path.join(prefix, 'MakerWare'),
            MB_EGG_DIR=os.path.join(prefix, 'MakerWare', 'python'))

    # These were getting set ----ing everywhere. There is almost no
    # situation where you would want to build against a sibling and
    # install to a directory where a different version of that sibling
    # was installed, and this should be fine in all other situations.
    env.Append(
        LIBPATH=env['MB_LIB_DIR'],
        CPPPATH=env['MB_INCLUDE_DIR'])

    # OSX doesn't use the standard link lines
    if env.MBIsMac():
        # add the fake root frameworks path
        env['MB_FRAMEWORK_DIR'] = os.path.join(prefix, 'Library/Frameworks')

        if not env.MBUseDevelLibs():
            env.AppendUnique(FRAMEWORKPATH=[env['MB_FRAMEWORK_DIR']])


def set_compiler_flags(env):
    ''' Sets flags required by all projects.

        Really, this just does things needed by C++ projects,
        but it won't interfere with the python ones. '''
    if env.MBIsMac():
        env.Replace(CC='clang')
        env.Replace(CXX='clang++')
        env.Append(CXXFLAGS='-arch x86_64  -std=c++11 -stdlib=libc++ ' +
                             '-mmacosx-version-min=10.7 ' +
                             # Disabling this warning since this extension is
                             # used a lot in Qt header files
                             '-Wno-nested-anon-types')
        env.Append(CCFLAGS='-arch x86_64 -stdlib=libc++ ' +
                           '-mmacosx-version-min=10.7 ')
        env.Append(LINKFLAGS='-arch x86_64 -stdlib=libc++ ' +
                             '-mmacosx-version-min=10.7')
        env.Append(FRAMEWORKS='CoreFoundation')
    elif env.MBIsLinux():
        env.Append(CXXFLAGS='-std=c++11 ' +
                   # Disabling this warning since some of Eigen3's
                   # headers cause it to happen in our code
                   '-Wno-unused-local-typedefs')
        env.Append(LINKFLAGS='-std=c++11 ' +
                   # This fixes the need for LD_LIBRARY_PATH=/usr/lib/makerbot
                   '-Wl,-rpath,\'/usr/lib/makerbot\'')

def mb_set_lib_sym_name(env, name):
    if (env.MBIsMac() and
       (not env.MBUseDevelLibs()) and
       (env.get('MB_LIB_SYM_NAME', None) == None)):

        env.SetDefault(MB_LIB_SYM_NAME=name)

        libpath = os.path.join('/',
                               'Library',
                               'Frameworks',
                               name + '.framework',
                               'Versions',
                               env['MB_VERSION'],
                               name)
        if '-install_name' in env['LINKFLAGS']:
            nameindex = env['LINKFLAGS'].index('-install_name') + 1
            env['LINKFLAGS'][nameindex] = libpath
        else:
            env.Append(LINKFLAGS = ['-install_name', libpath])

        if '-current_version' not in env['LINKFLAGS']:
            env.Append(LINKFLAGS = ['-current_version', env['MB_VERSION']])

        if '-compatibility_version' not in env['LINKFLAGS']:
            env.Append(LINKFLAGS = ['-compatibility_version',
                                    env['MB_VERSION']])

def api_define(env, target_name):
    """Return the API macro name for specified target.

    For most targets this is the target name upcased with special
    characters removed and "_API" appended.

    A special case for JsonCpp is hardcoded as it is an external
    dependency and so does not conform to our naming standard.
    """
    if target_name == 'jsoncpp':
        return 'JSON_API'
    else:
        return re.sub('[-_]', '', target_name).upper() + '_API'

def define_api_visibility_public(env, target_name):
    """Set the API macro to make symbols public on g++/clang++."""
    if env.MBIsLinux() or env.MBIsMac():
        env.Append(CPPDEFINES={
            api_define(env, target_name):
            '__attribute__ ((visibility (\\"default\\")))'})

def define_api_nothing(env, target):
    env.Append(CPPDEFINES={api_define(env, target): ''})

def windows_debug_tweak(env, lib):
    if env.MBIsWindows() and env.MBDebugBuild():
        lib += 'd'
    return lib

def define_library_dependency(env, libname, relative_repository_dir,
                              include_subdir='include',
                              header_only=False):
    """Set up internal library dependencies.

    libname: base name of the library, e.g. 'foo' for libfoo.so or
    foo.dll

    relative_repository_dir: relative top-level path of the repository
    directory, e.g. '#/../foo'

    include_subdir: path of the header files relative to the
    relative_repository_dir argument, defaults to 'include'

    header_only: if true, only include path is set, not library or
    library path.

    """
    if 'MB_MOD_BUILD' in os.environ:
        lib_path = env['MB_LIB_DIR']
        include_path = env['MB_INCLUDE_DIR']
    else:
        if env.MBIsWindows():
            # Yeah, on windows we still put stuff in obj,
            # even without the 'variant dir'
            lib_path = os.path.join(relative_repository_dir, 'obj')
            include_path = os.path.join(relative_repository_dir, include_subdir)
        else:
            obj_dir = os.path.join(relative_repository_dir, env.MBVariantDir())
            lib_path = obj_dir
            include_path = os.path.join(obj_dir, include_subdir)


    if env.MBIsMac():
        # This is a hack to work around this SCons bug:
        #
        # scons.tigris.org/issues/show_bug.cgi?id=2123
        #
        # Basically SCons doesn't find header dependencies correctly
        # through framework directories, so add the sibling includes
        # instead. Without this, SCons may fail to rebuild a file
        # because it doesn't know that an included file changed.
        env.MBAddIncludePaths(include_path)

    env.MBAddDevelIncludePath(include_path)

    if not header_only:
        env.MBAddDevelLibPath(lib_path)
        env.MBAddLib(windows_debug_tweak(env, libname))
        if env.MBIsWindows():
            env.MBWindowsAddAPIImport(api_define(env, libname))
        else:
            define_api_visibility_public(env, libname)

def define_cmake_dependency(env, libname):
    prefix = env['MB_PREFIX']

    env.MBAddLib(libname, framework=False)

    if env.MBIsWindows():
        env.MBWindowsAddAPIImport(api_define(env, libname))
    else:
        define_api_visibility_public(env, libname)


def mb_depends_on_mb_core_utils(env):
    define_library_dependency(env, 'MBCoreUtils', '#/../MBCoreUtils',
                              header_only=True)

def mb_depends_on_mbqtutils(env):
    define_library_dependency(env, 'mbqtutils', '#/../libmbqtutils')

def mb_depends_on_json_cpp(env):
    define_cmake_dependency(env, 'jsoncpp')

def mb_depends_on_json_rpc(env):
    define_cmake_dependency(env, 'jsonrpc')

def mb_depends_on_mbcamera(env):
    define_library_dependency(env, 'mbcamera', '#/../mbcamera')

def mb_depends_on_thing(env):
    define_library_dependency(env, 'thing', '#/../libthing-surprise')
    env.MBDependsOnOpenMesh()

def mb_depends_on_conveyor(env):
    define_library_dependency(env, 'conveyor', '#/../conveyor')

def mb_depends_on_conveyor_ui(env):
    define_library_dependency(env, 'conveyor-ui', '#/../conveyor-ui')

def mb_depends_on_toolpathviz(env):
    define_library_dependency(env, 'toolpathviz', '#/../ToolPathViz')

def mb_depends_on_tinything(env):
    define_library_dependency(env, 'tinything', '#/../libtinything')

def mb_scons_tools_path(env, path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, path)

def _common_binary_stuff(env, target, binary):
    """Encapsulates stuff that we do on all binaries"""
    env.Alias(target, binary)
    if env.MBIsMac():
        version = SCons.Node.Python.Value(
            env.MBVersion() + '.' + env.MBVersionBuild())
        env.Depends(binary, version)


def mb_program(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        program = env.MBWindowsProgram(target, source, *args, **kwargs)
    else:
        program = env.Program(target, source, *args, **kwargs)
    _common_binary_stuff(env, target, program)
    return program

def set_shared_library_visibility_flags(env, target):
    # MSVC doesn't need a flag, it has this behavior by default
    if env.MBIsLinux() or env.MBIsMac():
        # Sad hack. Ted will probably yell at me when he sees
        # this. Basically there are issues with setting the visibility
        # flag when typeinfo is needed. Mostly we don't use typeinfo,
        # but OpenMesh does use dynamic_cast.
        #
        # For now we just disable this in the case of libthing, but it
        # might yet be possible to fix this properly with more
        # research.
        if target != 'thing':
            env.Append(CCFLAGS=['-fvisibility=hidden'])

def mb_shared_library(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        env.MBWindowsSetDefaultAPIExport(api_define(env, target))
        library = env.MBWindowsSharedLibrary(target, source, *args, **kwargs)
    else:
        define_api_visibility_public(env, target)
        set_shared_library_visibility_flags(env, target)
        env.MBSetLibSymName(target)
        library = env.SharedLibrary(target, source, *args, **kwargs)
    _common_binary_stuff(env, target, library)
    return library

def mb_static_library(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        env.MBWindowsSetDefaultAPIExport(api_define(env, target))
        library = env.MBWindowsStaticLibrary(target, source, *args, **kwargs)
    else:
        define_api_nothing(env, target)
        library = env.StaticLibrary(target, source, *args, **kwargs)
    _common_binary_stuff(env, target, library)
    return library

def mb_get_moc_files(env, sources):
    target = []
    sources = SCons.Util.flatten(sources)
    for source in sources:
        with open(str(env.File(os.path.join('#', str(source)))), 'r') as contents:
            while True:
                line = contents.readline()
                if line == '':
                    break
                if 'Q_OBJECT' in line:
                    # this explicit putting it in the variant dir relative
                    # to the root should satisfy both mac and windows
                    moc_file = os.path.join(
                            '#',
                            env.MBVariantDir(),
                            'moc',
                            'moc_${SOURCE.file}.cpp')
                    mocced = env.ExplicitMoc5(
                            moc_file,
                            env.File(source))
                    target.append(mocced)
                    break
    return target

def common_arguments(env):
    # TODO(ted):
    # For these two, I'd like to set it up so that mb_install can give us the default locations
    # that it uses, so we can include them in the help message
    env.MBAddOption(
        '--install-prefix',
        dest='install_prefix',
        nargs=1,
        type='string',
        action='store',
        default='',
        help='Sets the location to install everything to. (someone should fill in the defaults here).')

    env.MBAddOption(
        '--config-prefix',
        dest='config_prefix',
        nargs=1,
        type='string',
        action='store',
        default='',
        help='Sets the location to install configs to. (someone should fill in the defaults here).')


def generate(env):
    env.Tool('mb_sconstruct')

    common_arguments(env)

    env.Tool('vcxproj')

    env['MB_INSTALL_TARGETS'] = []

    # turn off automoccing
    env['QT5_AUTOSCAN'] = 0

    # make sure LIBS is initialized
    if 'LIBS' not in env or env['LIBS'] is None or env['LIBS'] is '':
        env['LIBS'] = []

    # Eigen hack:
    # Don't let eigen use alignment on 32 bit platforms. This allows us to
    # avoid making some far-reaching changes in Miracle-Grue with respect to
    # passing aligned types and storing types containing eigen types in std
    # containers.
    if ((env.MBIsWindows() and env.MBWindowsIs32Bit()) or
       (platform.machine() == 'i386')):
        env.Append(CPPDEFINES=['EIGEN_DONT_ALIGN'])

    # Unpleasant state tracker: in case MBInstallHeaders is called
    # multiple times on OSX, ensure that the symlink command isn't
    # created multiple times. Should find a more SCons-like way of
    # doing the symlink step.
    env[symlink_env_name] = False

    env.AddMethod(mb_install_lib, 'MBInstallLib')
    env.AddMethod(mb_install_headers, 'MBInstallHeaders')
    env.AddMethod(mb_install_bin, 'MBInstallBin')
    env.AddMethod(mb_install_resources, 'MBInstallResources')
    env.AddMethod(mb_install_config, 'MBInstallConfig')
    env.AddMethod(mb_install_app, 'MBInstallApp')
    env.AddMethod(mb_install_egg, 'MBInstallEgg')
    env.AddMethod(mb_install_system, 'MBInstallSystem')
    env.AddMethod(mb_create_install_target, 'MBCreateInstallTarget')

    env.AddMethod(mb_dist_egg, 'MBDistEgg')

    env.AddMethod(mb_add_lib, 'MBAddLib')
    env.AddMethod(mb_add_include_paths, 'MBAddIncludePaths')
    env.AddMethod(mb_add_standard_compiler_flags, 'MBAddStandardCompilerFlags')
    env.AddMethod(mb_add_devel_lib_path, 'MBAddDevelLibPath')
    env.AddMethod(mb_add_devel_include_path, 'MBAddDevelIncludePath')

    env.AddMethod(mb_set_lib_sym_name, 'MBSetLibSymName')

    env.AddMethod(mb_depends_on_mb_core_utils, 'MBDependsOnMBCoreUtils')
    env.AddMethod(mb_depends_on_mbqtutils, 'MBDependsOnMBQtUtils')
    env.AddMethod(mb_depends_on_json_cpp, 'MBDependsOnJsonCpp')
    env.AddMethod(mb_depends_on_json_rpc, 'MBDependsOnJsonRpc')
    env.AddMethod(mb_depends_on_mbcamera, 'MBDependsOnMBCamera')
    env.AddMethod(mb_depends_on_thing, 'MBDependsOnThing')
    env.AddMethod(mb_depends_on_conveyor, 'MBDependsOnConveyor')
    env.AddMethod(mb_depends_on_conveyor_ui, 'MBDependsOnConveyorUi')
    env.AddMethod(mb_depends_on_toolpathviz, 'MBDependsOnToolPathViz')
    env.AddMethod(mb_depends_on_tinything, 'MBDependsOnTinything')

    env.AddMethod(mb_scons_tools_path, 'MBSConsToolsPath')

    env.AddMethod(mb_shared_library, 'MBSharedLibrary')
    env.AddMethod(mb_static_library, 'MBStaticLibrary')
    env.AddMethod(mb_program, 'MBProgram')

    env.AddMethod(mb_get_moc_files, 'MBGetMocFiles')

    set_install_paths(env)
    set_compiler_flags(env)

    env.Tool('mb_test')

def exists(env) :
    return True
