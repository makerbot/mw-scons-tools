from SCons.Script import ARGUMENTS
#from SCons.FS import Dir
import sys, os
import glob

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

def mb_install_lib(env, source, name):
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
        targets.append(env.Install(env['MB_LIB_DIR'], source))
        if env.MBIsWindows():
            targets.append(env.Install(env['MB_BIN_DIR'], source))

    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_headers(env, source, name, dest='', make_current_link=False):
    targets = []
    if env.MBIsMac():
        framework = os.path.join(env['MB_FRAMEWORK_DIR'], name + '.framework')
        version_dir = os.path.join('Versions', env['MB_VERSION'])
        include_dir = os.path.join(version_dir, 'Headers')

        headers = env.rInstall(os.path.join(framework, include_dir), source)
        targets += headers

        #make relative symlinks between Current and the new version
        current_dir = 'Current'
        if make_current_link:
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
        targets.append(env.Command(os.path.join(framework, toplink),
                                   targets, 'cd ' + framework +
                                   ';ln -sf ' + os.path.join('Versions',
                                                            current_dir,
                                                            'Headers')
                                             + ' ' + toplink))
        
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
        lib_dir = prefix + '/SDK/mingw/lib'
        include_dir = prefix + '/SDK/mingw/include'

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
                                                 'share', 'makerbot', 'python'))
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

def mb_set_lib_sym_name(env, name):
    if env.MBIsMac() and not env.MBUseDevelLibs():
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
        


def generate(env):
    print "Loading MakerBot install tool"

    env['MB_INSTALL_TARGETS'] = []

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

    env.MBSetDefaultPrefix()
    env.MBSetInstallPaths()

def exists(env) :
	return True
