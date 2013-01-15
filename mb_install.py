from SCons.Script import ARGUMENTS
import sys, os

def rInstall(env, dest, src, pattern='*'):
    installs = []

    src_str = str(src)

    for curpath, dirnames, filenames in os.walk(src_str):
        relative = os.path.relpath(curpath, src_str)

        installs.append(env.Install(os.path.join(dest, relative),
                                    filter(lambda f:
                                               (os.path.exists(str(f)) and
                                                not os.path.isdir(str(f))),
                                           env.Glob(os.path.join(curpath, pattern)))))

    return installs

def mb_install_lib(env, source):
    target = env.Install(env['MB_LIB_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_headers(env, source):
    targets = env.rInstall(env['MB_INCLUDE_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_bin(env, source):
    target = env.Install(env['MB_BIN_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return target

def mb_install_resources(env, source):
    targets = env.rInstall(env['MB_CONFIG_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = targets)
    return targets

def mb_install_app(env, source):
    target = env.Install(env['MB_APP_DIR'], source)
    env.Append(MB_INSTALL_TARGETS = target)
    return targets

def create_install_target(env):
    env.Alias('install', env['MB_INSTALL_TARGETS'])

def set_default_prefix(env):
    #setup the default install root
    prefix = ARGUMENTS.get('install_prefix', '')

    if prefix == '':
        if sys.platform == 'linux2':
            prefix = '/usr'

        elif sys.platform == 'win32':
            if os.path.exists('c:/Program Files (x86)'):
                prefix = 'c:/Program Files (x86)/MakerBot'
            else:
                prefix = 'c:/Program Files/MakerBot'

    env.SetDefault(MB_PREFIX = prefix)


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
        env.Append(FRAMEWORKS = 'MakerBot')
    else:
        env.Append(LIBPATH = lib_dir)
        env.Append(CPPPATH = include_dir)

    env.SetDefault(MB_LIB_DIR = lib_dir,
                   MB_INCLUDE_DIR = include_dir)

    #setup other install locations

    if sys.platform == 'linux2':
        env.SetDefault(MB_BIN_DIR = prefix + '/bin',
                       MB_APP_DIR = prefix + '/bin',
                       MB_CONFIG_DIR = prefix + '/share/makerbot')
    elif sys.platform == 'darwin':
        env.SetDefault(MB_BIN_DIR = prefix + '/Library/MakerBot',
                       MB_CONFIG_DIR = prefix + '/Library/MakerBot',
                       MB_APP_DIR = prefix + '/Applications')
    elif sys.platform == 'win32':
        env.SetDefault(MB_BIN_DIR = prefix + '/MakerWare',
                       MB_APP_DIR = prefix + '/MakerWare',
                       MB_CONFIG_DIR = prefix + '/MakerWare')

    
def generate(env):
    print "Loading MakerBot install tool"

    env['MB_INSTALL_TARGETS'] = []

    env.AddMethod(rInstall, 'rInstall')

    env.AddMethod(mb_install_lib, 'MBInstallLib')
    env.AddMethod(mb_install_headers, 'MBInstallHeaders')
    env.AddMethod(mb_install_bin, 'MBInstallBin')
    env.AddMethod(mb_install_resources, 'MBInstallResource')
    env.AddMethod(mb_install_app, 'MBInstallApp')

    env.AddMethod(set_default_prefix, 'MBSetDefaultPrefix')
    env.AddMethod(set_install_paths, 'MBSetInstallPaths')
    env.AddMethod(create_install_target, 'MBCreateInstallTarget')
    
    env.MBSetDefaultPrefix()
    env.MBSetInstallPaths()

def exists(env) :
	return True
