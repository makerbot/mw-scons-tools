# Copyright 2013 MakerBot Industries

import fnmatch
import glob
import os
import re
import sys
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

MB_VTK_CPPPATH = 'MB_VTK_CPPPATH'
MB_VTK_LIBPATH = 'MB_VTK_LIBPATH'
MB_OPENCV_CPPPATH = 'MB_OPENCV_CPPPATH'
MB_OPENCV_LIBPATH = 'MB_OPENCV_LIBPATH'
MB_BOOST_CPPPATH = 'MB_BOOST_CPPPATH'
MB_BOOST_LIBPATH = 'MB_BOOST_LIBPATH'
MB_OPENMESH_CPPPATH = 'MB_OPENMESH_CPPPATH'
MB_OPENMESH_LIBPATH = 'MB_OPENMESH_LIBPATH'
MB_BOOST_64_CPPPATH = 'MB_BOOST_64_CPPPATH'
MB_BOOST_64_LIBPATH = 'MB_BOOST_64_LIBPATH'
MB_BOOST_32_CPPPATH = 'MB_BOOST_32_CPPPATH'
MB_BOOST_32_LIBPATH = 'MB_BOOST_32_LIBPATH'
MB_OPENMESH_64_CPPPATH = 'MB_OPENMESH_64_CPPPATH'
MB_OPENMESH_64_LIBPATH = 'MB_OPENMESH_64_LIBPATH'
MB_OPENMESH_64 = 'MB_OPENMESH_64'
MB_OPENMESH_32_CPPPATH = 'MB_OPENMESH_32_CPPPATH'
MB_OPENMESH_32_LIBPATH = 'MB_OPENMESH_32_LIBPATH'
MB_OPENMESH_32 = 'MB_OPENMESH_32'
MB_THIRD_PARTY = 'MB_THIRD_PARTY'

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

    env_vars = [
            MB_VTK_CPPPATH,
            MB_VTK_LIBPATH,
            MB_OPENCV_CPPPATH,
            MB_OPENCV_LIBPATH,
            MB_BOOST_CPPPATH,
            MB_BOOST_LIBPATH,
            MB_OPENMESH_CPPPATH,
            MB_OPENMESH_LIBPATH,
            MB_BOOST_64_CPPPATH,
            MB_BOOST_64_LIBPATH,
            MB_BOOST_32_CPPPATH,
            MB_BOOST_32_LIBPATH,
            MB_OPENMESH_64_CPPPATH,
            MB_OPENMESH_64_LIBPATH,
            MB_OPENMESH_64,
            MB_OPENMESH_32_CPPPATH,
            MB_OPENMESH_32_LIBPATH,
            MB_OPENMESH_32,
            MB_THIRD_PARTY]
    for ev in env_vars:
        flag = ev.lower()
        flag = re.sub('_', '-', flag)
        env.MBAddOption(
            '--' + flag,
            dest=ev,
            action='store',
            help='Sets the value of ' + ev)


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
def mb_recursive_file_glob(env, root, pattern, exclude = None):
    """Recursively search in 'root' for files matching 'pattern'

    Returns a list of matches of type SCons.Node.FS.File.

    If exclude is not None, it should be a glob pattern or list of
    glob patterns. Any results matching a glob in exclude will be
    excluded from the returned list."""
    def excluded(filename, exclude):
        if exclude:
            if isinstance(exclude, str):
                exclude = [exclude]
            for pattern in exclude:
                if fnmatch.fnmatch(filename, pattern):
                    return True
        return False

    matches = []
    if root.startswith('#'):
        raise Exception('Directories starting with "#" not supported yet')
    project_root = env.Dir('#').abspath
    for parent, dirnames, filenames in os.walk(os.path.join(
            project_root, root)):
        for filename in fnmatch.filter(filenames, pattern):
            if not excluded(filename, exclude):
                p = os.path.join(parent, filename)
                rp = os.path.relpath(p, project_root)
                matches.append(env.File(rp))
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
    ''' Get a variable from the environment interpreted as a path.

        If it's a list return it as-is,
        If it's a string break it on the path separator (either ':' or ';') '''
    var = env.GetOption(pathname)

    if None == var:
        try:
            var = env[pathname]
        except KeyError:
            raise KeyError(
                'This SConscript expects you to have an '
                'environment variable ' + pathname + ' defined.')
    if SCons.Util.is_List(var):
        return var
    else:
        if env.MBIsWindows:
            return var.split(';')
        else:
            return value.split(':')

def set_third_party_paths(env):
    ''' Sets the default locations for third-party libs and headers.

        We assume that if anything is in a non-standard location the
        user has set the appropriate environment variable. '''
    e = os.environ
    # SetDefault sets if the variable is not already set.
    if env.MBIsMac():
        env.SetDefault(
            MB_VTK_CPPPATH =
                e.get(MB_VTK_CPPPATH,
                '/usr/local/vtk/include/vtk-5.10'),
            MB_VTK_LIBPATH =
                e.get(MB_VTK_LIBPATH,
                '/usr/local/vtk/lib/vtk-5.10'),
            MB_OPENCV_CPPPATH =
                e.get(MB_OPENCV_CPPPATH,
                '/usr/local/opencv/include'),
            MB_OPENCV_LIBPATH =
                e.get(MB_OPENCV_LIBPATH,
                '/usr/local/opencv/lib'),
            MB_BOOST_CPPPATH =
                e.get(MB_BOOST_CPPPATH,
                '/usr/local/boost/include/boost-1_53'),
            MB_BOOST_LIBPATH =
                e.get(MB_BOOST_LIBPATH,
                '/usr/local/boost/lib'),
            MB_OPENMESH_CPPPATH =
                e.get(MB_OPENMESH_CPPPATH,
                '/usr/local/openmesh/include'),
            MB_OPENMESH_LIBPATH =
                e.get(MB_OPENMESH_LIBPATH,
                '/usr/local/openmesh/lib/OpenMesh'))
    elif env.MBIsLinux():
        env.SetDefault(
            MB_VTK_CPPPATH = e.get(MB_VTK_CPPPATH, []),
            MB_VTK_LIBPATH = e.get(MB_VTK_LIBPATH, []),
            MB_OPENCV_CPPPATH = e.get(MB_OPENCV_CPPPATH, []),
            MB_OPENCV_LIBPATH = e.get(MB_OPENCV_LIBPATH, []),
            MB_BOOST_CPPPATH = e.get(MB_BOOST_CPPPATH, []),
            MB_BOOST_LIBPATH = e.get(MB_BOOST_LIBPATH, []),
            MB_OPENMESH_CPPPATH = e.get(MB_OPENMESH_CPPPATH, []),
            MB_OPENMESH_LIBPATH = e.get(MB_OPENMESH_LIBPATH, []))
    elif env.MBIsWindows():
        env.SetDefault(
            MB_THIRD_PARTY = e.get(MB_THIRD_PARTY, []))
        third_party_dir = env[MB_THIRD_PARTY]
        env.SetDefault(
            MB_VTK_CPPPATH = e.get(MB_VTK_CPPPATH, []),
            MB_VTK_LIBPATH = e.get(MB_VTK_LIBPATH, []),
            MB_OPENCV_CPPPATH = e.get(MB_OPENCV_CPPPATH, []),
            MB_OPENCV_LIBPATH = e.get(MB_OPENCV_LIBPATH, []),
            MB_BOOST_64_CPPPATH =
                e.get(MB_BOOST_64_CPPPATH,
                os.path.join(third_party_dir, 'Boost-1.53', 'boost-64', 'include')),
            MB_BOOST_64_LIBPATH =
                e.get(MB_BOOST_64_LIBPATH,
                os.path.join(third_party_dir, 'Boost-1.53', 'boost-64', 'lib')),
            MB_BOOST_32_CPPPATH =
                e.get(MB_BOOST_32_CPPPATH,
                os.path.join(third_party_dir, 'Boost-1.53', 'boost-32', 'include')),
            MB_BOOST_32_LIBPATH =
                e.get(MB_BOOST_32_LIBPATH,
                os.path.join(third_party_dir, 'Boost-1.53', 'boost-32', 'lib')),
            MB_OPENMESH_64_CPPPATH =
                e.get(MB_OPENMESH_64_CPPPATH,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-64', 'include')),
            MB_OPENMESH_64_LIBPATH =
                e.get(MB_OPENMESH_64_LIBPATH,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-64', 'dll')),
            MB_OPENMESH_64 =
                e.get(MB_OPENMESH_64,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-64')),
            MB_OPENMESH_32_CPPPATH =
                e.get(MB_OPENMESH_32_CPPPATH,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-32', 'include')),
            MB_OPENMESH_32_LIBPATH =
                e.get(MB_OPENMESH_32_LIBPATH,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-32', 'dll')),
            MB_OPENMESH_32 =
                e.get(MB_OPENMESH_32,
                os.path.join(third_party_dir, 'OpenMesh-2.4', 'openmesh-32')))

def mb_depends_on_openmesh(env):
    if env.MBIsWindows():
        bitness = '64' if env.MBWindowsIs64Bit() else '32'
        env.Append(LIBPATH = env.MBGetPath('MB_OPENMESH_' + bitness + '_LIBPATH'))
        env.Append(CPPPATH = env.MBGetPath('MB_OPENMESH_' + bitness + '_CPPPATH'))
        env.Append(CPPDEFINES = '_USE_MATH_DEFINES')
    else:
        env.Append(LIBPATH = env.MBGetPath(MB_OPENMESH_LIBPATH))
        env.Append(CPPPATH = env.MBGetPath(MB_OPENMESH_CPPPATH))

    if env.MBDebugBuild():
        env.Append(CPPDEFINES = 'OPENMESH_DEBUG')

    env.Append(LIBS = ['OpenMeshCore', 'OpenMeshTools'])

def mb_depends_on_boost(env):
    if env.MBIsWindows():
        bitness = '64' if env.MBWindowsIs64Bit() else '32'
        env.Append(LIBPATH = env.MBGetPath('MB_BOOST_' + bitness + '_LIBPATH'))
        env.Append(CPPPATH = env.MBGetPath('MB_BOOST_' + bitness + '_CPPPATH'))
    else:
        env.Append(LIBPATH = env.MBGetPath(MB_BOOST_LIBPATH))
        env.Append(CPPPATH = env.MBGetPath(MB_BOOST_CPPPATH))

def mb_depends_on_opencv(env):
    env.Append(LIBPATH = env.MBGetPath(MB_OPENCV_LIBPATH))
    env.Append(CPPPATH = env.MBGetPath(MB_OPENCV_CPPPATH))

def mb_depends_on_vtk(env):
    env.Append(LIBPATH = env.MBGetPath(MB_VTK_LIBPATH))
    env.Append(CPPPATH = env.MBGetPath(MB_VTK_CPPPATH))

def mb_add_openmp_option(env):
    """Add a '--disable-openmp' command-line option"""
    env.MBAddOption(
        '--disable-openmp',
        dest='openmp_enabled',
        action='store_false',
        help='Turn off OpenMP')

def mb_setup_openmp(env):
    """Add OpenMP compiler flags if OpenMP is supported and enabled

    Calls mb_add_openmp_option() to add a SCons flag for disabling
    OpenMP.

    If OpenMP is enabled, the appropriate flags are set for MSVC and
    G++. Clang does not support OpenMP yet."""
    mb_add_openmp_option(env)
    if env.GetOption('openmp_enabled') != False:
        compiler = env['CXX']
        if compiler == 'g++':
            print('OpenMP enabled')
            env.Append(CCFLAGS=['-fopenmp'])
            env.Append(LINKFLAGS=['-fopenmp'])
        elif env.MBIsWindows():
            # This is technically wrong, should check if compiler is
            # MVSC rather than just "on Windows"
            print('OpenMP enabled')
            env.Append(CCFLAGS=['/openmp'])
        else:
            # clang doesn't support OpenMP yet
            print('OpenMP enabled but not supported')
    else:
        print('OpenMP disabled')

def generate(env):
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

    env.AddMethod(mb_depends_on_openmesh, 'MBDependsOnOpenMesh')
    env.AddMethod(mb_depends_on_boost, 'MBDependsOnBoost')
    env.AddMethod(mb_depends_on_opencv, 'MBDependsOnOpenCV')
    env.AddMethod(mb_depends_on_vtk, 'MBDependsOnVTK')

    env.AddMethod(mb_setup_openmp, 'MBSetupOpenMP')

    set_third_party_paths(env)

def exists(env) :
    return True
