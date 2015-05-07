
import os
import re
import subprocess
import sys


def load_version(env):
    # extract the build version
    with open(str(env.File('#/mb_version'))) as version_file:
        env['MB_VERSION'] = version_file.readline()

    env['MB_VERSION'] = env['MB_VERSION'].strip()

    version_list = [int(v) for v in env['MB_VERSION'].split('.')]
    if len(version_list) != 3:
        raise Exception('mb_version must contain three period-separated parts')

    env['MB_VERSION_MAJOR'] = version_list[0]
    env['MB_VERSION_MINOR'] = version_list[1]
    env['MB_VERSION_POINT'] = version_list[2]
    env['MB_VERSION_BUILD'] = os.environ.get('BUILD_NUMBER', '1337')


def mb_version(env):
    ''' Returns the version number for the current build. '''
    return env['MB_VERSION']


def mb_version_major(env):
    ''' Returns the major version number.

        e.g. for a build version 1.2.3.4, this would return 1
    '''
    return env['MB_VERSION_MAJOR']


def mb_version_minor(env):
    ''' Returns the minor version number.

        e.g. for a build version 1.2.3.4, this would return 2
    '''
    return env['MB_VERSION_MINOR']


def mb_version_point(env):
    ''' Returns the point version number.

        e.g. for a build version 1.2.3.4, this would return 3
    '''
    return env['MB_VERSION_POINT']


def mb_version_build(env):
    ''' Returns the jenkins build number (the value of the BUILD_NUMBER
        environment variable) or 1337 for a dev build. '''
    return env['MB_VERSION_BUILD']


def generate(env):
    env.Tool('options')

    load_version(env)

    env.AddMethod(mb_version, 'MBVersion')
    env.AddMethod(mb_version_major, 'MBVersionMajor')
    env.AddMethod(mb_version_minor, 'MBVersionMinor')
    env.AddMethod(mb_version_point, 'MBVersionPoint')
    env.AddMethod(mb_version_build, 'MBVersionBuild')


def exists(env):
    return True
