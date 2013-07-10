from SCons.Script import AddOption, GetOption
from optparse import OptionConflictError
import glob
import os
import sys

# Some conventions to keep this sane:
#  * function definitions are in lowercase_with_underscores
#  * if the function is exported by the tool, it starts with mb_
#  * functions/builders are exported in camelcase, including the initial MB
#  * functions are added in the same order as they appear in this file
# Feel free to change the conventions if you think they're wrong,
# just make sure to update everything to match those conventions

# Set up command line args used by every scons script
def common_arguments():
    # This is pretty silly, but because we load this tool multiple times
    # these options can be loaded twice, which raises an error.
    # This error can be safely ignored.
    try:
        AddOption(
            '--debug-build',
            dest='debug_build',
            action='store_true',
            help='Builds in debug mode')

        AddOption(
            '--devel-libs',
            dest='devel_libs',
            action='store_true',
            help='Uses sibling repositories for libraries, rather than using installed libs.')

        AddOption(
            '--build-tests',
            dest='build_tests',
            action='store_true',
            help='Builds the test suite (if one exists)')

        AddOption(
            '--run-tests',
            dest='run_tests',
            action='store_true',
            help='Runs the test suite (if one exists). Does not imply --build-tests.')

    except OptionConflictError:
        pass

# Accessors for the common arguments
def mb_use_devel_libs(env):
    return GetOption('devel_libs')

def mb_debug_build(env):
    return GetOption('debug_build')

def mb_build_tests(env):
    return GetOption('build_tests')

def mb_run_tests(env):
    return GetOption('run_tests')


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


def generate(env):
    common_arguments()

    env.AddMethod(mb_use_devel_libs, 'MBUseDevelLibs')
    env.AddMethod(mb_debug_build, 'MBDebugBuild')
    env.AddMethod(mb_build_tests, 'MBBuildTests')
    env.AddMethod(mb_run_tests, 'MBRunTests')

    env.AddMethod(mb_is_windows, 'MBIsWindows')
    env.AddMethod(mb_is_linux, 'MBIsLinux')
    env.AddMethod(mb_is_mac, 'MBIsMac')

    env.AddMethod(mb_glob, 'MBGlob')


def exists(env) :
    return True