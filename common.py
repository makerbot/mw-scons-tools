# Copyright 2013 MakerBot Industries

import fnmatch
import glob
import os
import sys

'''
Some conventions to keep this sane:
  * function definitions are in lowercase_with_underscores
  * if the function is exported by the tool, it starts with mb_
  * functions/builders are exported in camelcase, including the initial MB
  * functions are added in the same order as they appear in this file
Feel free to change the conventions if you think they're wrong,
just make sure to update everything to match those conventions
'''

# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--debug-build',
        dest='debug_build',
        action='store_true',
        help='Builds in debug mode')

    env.MBAddOption(
        '--no-devel-libs',
        dest='devel_libs',
        action='store_false',
        default=True,
        help='Uses sibling repositories for libraries, rather than using installed libs.')

    env.MBAddOption(
        '--build-tests',
        dest='build_tests',
        action='store_true',
        help='Builds the test suite (if one exists)')

    env.MBAddOption(
        '--run-tests',
        dest='run_tests',
        action='store_true',
        help='Runs the test suite (if one exists). Does not imply --build-tests.')


# Accessors for the common arguments
def mb_use_devel_libs(env):
    return env.MBGetOption('devel_libs')

def mb_debug_build(env):
    return env.MBGetOption('debug_build')

def mb_build_tests(env):
    return env.MBGetOption('build_tests')

def mb_run_tests(env):
    return env.MBGetOption('run_tests')


# Utilities for detecting platform
_is_windows = ('win32' == sys.platform)
_is_linux = (sys.platform.startswith('linux'))
_is_mac = ('darwin' == sys.platform)

def mb_is_windows(env):
  return _is_windows

def mb_is_linux(env):
  return _is_linux

def mb_is_mac(env):
  return _is_mac

# This is a special glob made by Joe Sadusk
def mb_glob(env, path):
    (head, tail) = os.path.split(path)
    return glob.glob(os.path.join(str(env.Dir(head)), tail))

# This is a special glob made by NicholasBishop
def mb_recursive_file_glob(env, root, pattern):
    '''Recursively search in 'root' for files matching 'pattern'

    Returns a list of matches of type SCons.Node.FS.File'''
    def path_without_first_component(path):
        return os.sep.join(path.split(os.sep)[1:])

    matches = []
    if root.startswith('#'):
        raise Exception('Directories starting with "#" not supported yet')
    for parent, dirnames, filenames in os.walk(os.path.join('..', root)):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(env.File(
                    path_without_first_component(os.path.join(parent, filename))))
    return matches

# I'm not sure who made this, but we use it for all of our python globbing
def mb_magic_python_glob(env, dir):
    files = []
    for curpath, dirnames, filenames in os.walk(str(env.Dir(dir))):
        files.append(
            filter(lambda f:
                (os.path.exists(str(f)) and not os.path.isdir(str(f))),
                env.Glob(os.path.join(curpath, '*.py'))))
    return files

def mb_get_path(env, pathname):
    ''' Get a variable from the environment interpreted as a path,
        i.e. as a list of paths. '''
    try:
        var = env[pathname]
    except KeyError:
        raise KeyError(
            'This SConscript expects you to have an '
            'environment variable ' + pathname + ' defined.')
    if env.MBIsWindows:
        return var.split(';')
    else:
        return value.split(':')

def set_third_party_paths(env):
    ''' Sets the default locations for third-party libs and headers.

        We assume that if anything is in a non-standard location the
        user has set the appropriate environment variable. '''
    # SetDefault sets if the variable is not already set.
    if env.MBIsMac():
        env.SetDefault(
            MB_VTK_CPPPATH = os.path.join('/usr', 'local', 'vtk', 'include', 'vtk-5.10'),
            MB_VTK_LIBPATH = os.path.join('/usr', 'local', 'vtk', 'lib', 'vtk-5.10'),
            MB_OPENCV_CPPPATH = os.path.join('/usr', 'local', 'opencv', 'include'),
            MB_OPENCV_LIBPATH = os.path.join('/usr', 'local', 'opencv', 'lib'),
            MB_BOOST_CPPPATH = os.path.join('/usr', 'local', 'boost', 'include', 'boost-1_53'),
            MB_BOOST_LIBPATH = os.path.join('/usr', 'local', 'boost', 'lib'))
    elif env.MBIsWindows():
        env.SetDefault(
            MB_BOOST_64_CPPPATH = os.path.join('C:', 'Boost', 'include', 'boost-1_53'),
            MB_BOOST_64_LIBPATH = os.path.join('C:', 'Boost', 'x64'),
            MB_BOOST_32_CPPPATH = os.path.join('C:', 'Boost', 'include', 'boost-1_53'),
            MB_BOOST_32_LIBPATH = os.path.join('C:', 'Boost', 'x86'))

def generate(env):
    tool_exists = 'MB_COMMON_TOOL_LOADED'
    if env.get(tool_exists, False):
        print 'tool "common" being loaded multiple times'
    else:
        env[tool_exists] = True

    env.Tool('options')

    common_arguments(env)

    env.AddMethod(mb_use_devel_libs, 'MBUseDevelLibs')
    env.AddMethod(mb_debug_build, 'MBDebugBuild')
    env.AddMethod(mb_build_tests, 'MBBuildTests')
    env.AddMethod(mb_run_tests, 'MBRunTests')

    env.AddMethod(mb_is_windows, 'MBIsWindows')
    env.AddMethod(mb_is_linux, 'MBIsLinux')
    env.AddMethod(mb_is_mac, 'MBIsMac')

    env.AddMethod(mb_glob, 'MBGlob')
    env.AddMethod(mb_recursive_file_glob, 'MBRecursiveFileGlob')
    env.AddMethod(mb_magic_python_glob, 'MBMagicPythonGlob')

    env.AddMethod(mb_get_path, 'MBGetPath')

    set_third_party_paths(env)

def exists(env) :
    return True