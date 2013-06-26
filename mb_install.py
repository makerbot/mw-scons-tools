from SCons.Script import ARGUMENTS
#from SCons.FS import Dir
import sys, os
import glob
import string
import re

symlink_env_name = 'MB_MAC_FRAMEWORK_HEADER_SYMLINK_DONE'

def rInstall(env, dest, src):
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

def mb_glob(env, path):
    (head, tail) = os.path.split(path)
    return glob.glob(os.path.join(str(env.Dir(head)), tail))

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
                                   + ';ln -sf ' +
                                   env['MB_VERSION'] + ' ' + current_dir)
        targets.append(current_link)

        #make a relative symlink for the current lib
        targets.append(env.Command(os.path.join(framework, name),
                                   current_link, 'cd ' + framework +
                                   ';ln -sf ' +
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
        # TODO(nicholasbishop): this will break with more levels of
        # subdirectories
        #
        # TODO(nicholasbishop): IMO a more explicit interface that
        # acknowledges better the differences between platforms might
        # be a better idea.
        split_name = os.path.split(name)
        if split_name[0]:
            framework_name = split_name[0]
            include_subdir = split_name[1]
        else:
            framework_name = split_name[1]
            include_subdir = ''
        framework_name += '.framework'

        framework = os.path.join(env['MB_FRAMEWORK_DIR'], framework_name)
        version_dir = os.path.join('Versions', env['MB_VERSION'])
        include_dir = os.path.join(version_dir, 'Headers', include_subdir)

        headers = env.rInstall(os.path.join(framework, include_dir), source)
        targets += headers

        #make relative symlinks between Current and the new version
        current_dir = 'Current'
        if make_current_link and not env[symlink_env_name]:
            current_link = env.Command(os.path.join(framework, 'Versions',
                                                    current_dir),
                                       headers,
                                       'cd ' + os.path.join(framework,
                                                            'Versions')
                                       + ';ln -sf ' +
                                       env['MB_VERSION'] + ' ' + current_dir)
            targets.append(current_link)

        #make a relative symlink for the current headers
        toplink = os.path.join(framework, 'Headers')
        target_path = os.path.join(framework, toplink)
        if not env[symlink_env_name]:
            targets.append(env.Command(
                target_path,
                targets, 'cd ' + framework +
                ';ln -sf ' + os.path.join('Versions',
                                          current_dir,
                                          'Headers')
                + ' ' + toplink))

        env[symlink_env_name] = True

    else:
        targets = env.rInstall(os.path.join(env['MB_INCLUDE_DIR'],
                                            os.path.join(dest, name)),
                               source)

    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_bin(env, source):
    target = env.Install(env['MB_BIN_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_resources(env, source, subdir=''):
    targets = env.rInstall(os.path.join(env['MB_RESOURCE_DIR'], subdir), source)
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

def create_install_target(env):
    env.Alias('install', env['MB_INSTALL_TARGETS'])

def mb_use_devel_libs(env):
    return ARGUMENTS.get('devel_libs', '') is not ''

def mb_debug_build(env):
    return ARGUMENTS.get('debug_build', '') is not ''

def mb_build_tests(env):
    return ARGUMENTS.get('build_tests', '') is not ''

def mb_run_tests(env):
    return ARGUMENTS.get('run_tests', '') is not ''

def mb_add_lib(env, name):
    if env.MBIsMac() and not env.MBUseDevelLibs():
        env.Append(CCFLAGS = ['-framework', name])
        env.Append(LINKFLAGS = ['-framework', name])
    else:
        env.Append(LIBS = name)

def add_devel_lib_path(env, path):
    if ARGUMENTS.get('devel_libs', '') is not '':
        env.Prepend(LIBPATH = [str(env.Dir(path))])

def add_devel_include_path(env, path):
    if ARGUMENTS.get('devel_libs', '') is not '':
        env.Prepend(CPPPATH = [str(env.Dir(path))])

def set_default_prefix(env):
    #setup the default install root
    prefix = ARGUMENTS.get('install_prefix', '')
    config_prefix = ARGUMENTS.get('config_prefix', '')

    #if the user doesn't set either prefix, put configs in /etc
    if config_prefix == '':
        if sys.platform == 'linux2':
            if prefix == '':
                config_prefix = '/etc'
            else:
                config_prefix = os.path.join(prefix, 'etc')

    if prefix == '':
        if sys.platform == 'linux2':
            if config_prefix == '':
                config_prefix = '/etc'
            prefix = '/usr'

        elif sys.platform == 'win32':
            if os.path.exists('c:/Program Files (x86)'):
                prefix = 'c:/Program Files (x86)/MakerBot'
            else:
                prefix = 'c:/Program Files/MakerBot'
        elif sys.platform == 'darwin':
            prefix = '/'

    env.SetDefault(MB_PREFIX = prefix)
    if config_prefix != '':
        env.SetDefault(MB_CONFIG_DIR = config_prefix)


def set_install_paths(env):
    prefix = env['MB_PREFIX']

    #setup sdk locations
    if sys.platform == 'linux2':
        lib_dir = prefix + '/lib'
        include_dir = prefix + '/include'

    elif sys.platform == 'darwin':
        lib_dir = prefix + '/Library/Frameworks/MakerBot.framework/Libraries'
        include_dir = prefix + '/Library/Frameworks/MakerBot.framework/Include'

    elif sys.platform == 'win32':
        lib_dir = prefix + '/SDK/msvc11/lib'
        include_dir = prefix + '/SDK/msvc11/include'

    #OSX doesn't use the standard link lines
    if sys.platform == 'darwin':
        #add the fake root frameworks path
        env['MB_FRAMEWORK_DIR'] = os.path.join(prefix, 'Library/Frameworks')

        if not env.MBUseDevelLibs():
            env.Append(CCFLAGS = ['-F' + env['MB_FRAMEWORK_DIR']])
            env.Append(LINKFLAGS = ['-F' + env['MB_FRAMEWORK_DIR']])
    else:
        env.Append(LIBPATH = [lib_dir])
        env.Append(CPPPATH = [include_dir])

    env.SetDefault(MB_LIB_DIR = lib_dir,
                   MB_INCLUDE_DIR = include_dir)

    #setup other install locations

    if sys.platform == 'linux2':
        env.SetDefault(MB_BIN_DIR = os.path.join(prefix, 'bin'),
                       MB_APP_DIR = os.path.join(prefix, 'bin'),
                       MB_RESOURCE_DIR = os.path.join(prefix,
                                                      'share', 'makerbot'),
                       MB_CONFIG_DIR = os.path.join(prefix, 'etc'),
                       MB_EGG_DIR = os.path.join(prefix,
                                                 'share', 'makerbot', 'python'),
                       MB_SYSTEM_EGG_DIR = os.path.join('/', 'usr', 'share',
                                                         'makerbot', 'python'))
    elif sys.platform == 'darwin':
        env.SetDefault(MB_BIN_DIR = os.path.join(prefix, 'Library', 'MakerBot'),
                       MB_RESOURCE_DIR = os.path.join(prefix,
                                                      'Library', 'MakerBot'),
                       MB_CONFIG_DIR = os.path.join(prefix,
                                                    'Library', 'MakerBot'),
                       MB_APP_DIR = os.path.join(prefix, 'Applications'),
                       MB_EGG_DIR = os.path.join(prefix, 'Library', 'MakerBot',
                                                 'python'))
    elif sys.platform == 'win32':
        env.SetDefault(MB_BIN_DIR = os.path.join(prefix, 'MakerWare'),
                       MB_APP_DIR = os.path.join(prefix, 'MakerWare'),
                       MB_RESOURCE_DIR = os.path.join(prefix, 'MakerWare'),
                       MB_CONFIG_DIR = os.path.join(prefix, 'MakerWare'),
                       MB_EGG_DIR = os.path.join(prefix, 'MakerWare', 'python'))

    #extract the build version
    version_file = open(str(env.File('#/mb_version')))
    env['MB_VERSION'] = version_file.readline()
    version_file.close()
    env['MB_VERSION'] = string.strip(env['MB_VERSION'])
    env.Append(CPPDEFINES='MB_VERSION_STR=\\\"%s\\\"'%(env['MB_VERSION'],))

    #make sure LIBS is initialized
    if 'LIBS' not in env or env['LIBS'] is None or env['LIBS'] is '':
        env['LIBS'] = []

_is_windows = ('win32' == sys.platform)
_is_linux = (sys.platform.startswith('linux'))
_is_mac = ('darwin' == sys.platform)

def mb_is_windows(env):
  return _is_windows

def mb_is_linux(env):
  return _is_linux

def mb_is_mac(env):
  return _is_mac

def mb_prepare_boost(env):
    boost_dir = os.environ.get('MB_BOOST_DIR')
    if boost_dir is None:
        print '\n======================================================='
        print 'MB_BOOST_DIR not specified'
        print ''
    else:
        include_dir = os.path.join(boost_dir, 'include')
        boost_version_re = re.compile('^boost-(?P<major>\d+)_(?P<minor>\d+)$')
        #get the list of boost versions available
        versions = [(int(match.group('major')), int(match.group('minor')))
                for match in (boost_version_re.match(a)
                for a in os.listdir(include_dir)) if match]
        #sort them by major,minor then pick the latest
        subdir = 'boost-{}_{}'.format(*(sorted(versions)[-1]))
        include = os.path.join(include_dir, subdir)
        lib = os.path.join(boost_dir, 'lib')
        env.Append(CPPPATH = [include])
        env.Append(LIBPATH = lib)
        print '\n======================================================='
        print 'Boost directories: '
        print include
        print lib
        print ''

def mb_set_compiler_flags(env):
    if env.MBIsMac():
        env.Replace(CC='clang')
        env.Replace(CXX='clang++')
        env.Append(CXXFLAGS='-arch x86_64 -arch i386 '+
                   '-std=c++11 -stdlib=libc++ -mmacosx-version-min=10.6 '+
                   '-I/usr/local/clang/include '+
                   '-I/usr/local/clang/include/c++/v1 ' +
                   # Disabling this warning since this extension is
                   # used a lot in Qt header files
                   '-Wno-nested-anon-types')
        env.Append(CCFLAGS='-arch x86_64 -arch i386 '+
                   '-stdlib=libc++ -mmacosx-version-min=10.6 '+
                   '-I/usr/local/clang/include')
        env.Append(LINKFLAGS='-arch x86_64 -arch i386 -stdlib=libc++ '+
                   '-mmacosx-version-min=10.6 -L/usr/local/clang/lib')
        env.Append(FRAMEWORKS='CoreFoundation')
    elif env.MBIsLinux():
        env.Append(CXXFLAGS='-std=c++11')
        env.Append(LINKFLAGS='-std=c++11')

def mb_set_lib_sym_name(env, name):
    if env.MBIsMac() and not env.MBUseDevelLibs():
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

kProgramType = 'exe'
kStaticLibraryType = 'lib'
kDynamicLibraryType = 'dll'

def mb_msbuild(env, target, sources, target_type, *args, **kwargs):
    # Horrible hack:
    # strip the target name down to the 'base name'
    # (i.e. without variant dir) and use that as the
    # name of the vcxproj to build.
    # I'm also not sure we'll ever get more than one target,
    # so I'll leave that non-functional until we hit that case.
    basename = os.path.basename(target)
    vcxproj = os.path.join(
        'win',
        'vcxproj',
        basename,
        basename + '.vcxproj')

    if 'platform' in kwargs:
        platform = kwargs['platform']
    else:
        platform = 'x64'

    command = [
        'msbuild',
        '/p:MBConfiguration=' + ('Debug' if env.MBDebugBuild() else 'Release'),
        '/p:Platform=' + platform,
        vcxproj
    ]

    # Horrible hack:
    # fake the files we expect to come out of this
    expandedname = basename
    if env.MBDebugBuild():
        expandedname += 'd'

    if target_type == kStaticLibraryType:
        expandedname = 'lib' + expandedname

    targets = [
        '#/obj/' + platform + '/' + expandedname + '.' + target_type,
        '#/obj/' + platform + '/' + expandedname + '.pdb'
    ]

    if target_type == kDynamicLibraryType:
        targets.append('#/obj/' + platform + '/' + expandedname + '.lib')

    # add the vxcproj to the sources list
    # I think this tells scons that if the
    # vcxproj changes this requires a rebuild
    sources += [vcxproj]

    return env.Command(targets, sources, ' '.join(command))

def mb_program(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        return env.MBMSBuild(target, source, kProgramType, *args, **kwargs)
    else:
        return env.Program(target, source, *args, **kwargs);

def mb_shared_library(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        return env.MBMSBuild(target, source, kDynamicLibraryType, *args, **kwargs)
    else:
        return env.SharedLibrary(target, source, *args, **kwargs)

def mb_static_library(env, target, source, *args, **kwargs):
    if env.MBIsWindows():
        return env.MBMSBuild(target, source, kStaticLibraryType, *args, **kwargs)
    else:
        return env.StaticLibrary(target, source, *args, **kwargs)

def generate(env):
    print "Loading MakerBot install tool"

    env['MB_INSTALL_TARGETS'] = []

    # Unpleasant state tracker: in case MBInstallHeaders is called
    # multiple times on OSX, ensure that the symlink command isn't
    # created multiple times. Should find a more SCons-like way of
    # doing the symlink step.
    env[symlink_env_name] = False

    env.AddMethod(rInstall, 'rInstall')

    env.AddMethod(mb_install_lib, 'MBInstallLib')
    env.AddMethod(mb_install_headers, 'MBInstallHeaders')
    env.AddMethod(mb_install_bin, 'MBInstallBin')
    env.AddMethod(mb_install_resources, 'MBInstallResources')
    env.AddMethod(mb_install_app, 'MBInstallApp')
    env.AddMethod(mb_install_egg, 'MBInstallEgg')
    env.AddMethod(mb_install_config, 'MBInstallConfig')
    env.AddMethod(mb_install_system, 'MBInstallSystem')

    env.AddMethod(set_default_prefix, 'MBSetDefaultPrefix')
    env.AddMethod(set_install_paths, 'MBSetInstallPaths')
    env.AddMethod(create_install_target, 'MBCreateInstallTarget')
    env.AddMethod(add_devel_lib_path, 'MBAddDevelLibPath')
    env.AddMethod(add_devel_include_path, 'MBAddDevelIncludePath')
    env.AddMethod(mb_add_lib, 'MBAddLib')
    env.AddMethod(mb_set_lib_sym_name, 'MBSetLibSymName')
    env.AddMethod(mb_glob, 'MBGlob')

    env.AddMethod(mb_is_windows, 'MBIsWindows')
    env.AddMethod(mb_is_linux, 'MBIsLinux')
    env.AddMethod(mb_is_mac, 'MBIsMac')
    env.AddMethod(mb_use_devel_libs, 'MBUseDevelLibs')

    env.AddMethod(mb_debug_build, 'MBDebugBuild')
    env.AddMethod(mb_build_tests, 'MBBuildTests')
    env.AddMethod(mb_run_tests, 'MBRunTests')

    env.AddMethod(mb_msbuild, 'MBMSBuild')

    env.AddMethod(mb_shared_library, 'MBSharedLibrary')
    env.AddMethod(mb_static_library, 'MBStaticLibrary')
    env.AddMethod(mb_program, 'MBProgram')

    env.AddMethod(mb_prepare_boost, 'MBPrepareBoost')
    env.AddMethod(mb_set_compiler_flags, 'MBSetCompilerFlags')

    env.MBSetDefaultPrefix()
    env.MBSetInstallPaths()
    env.MBPrepareBoost()
    env.MBSetCompilerFlags()

def exists(env) :
    return True
