
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


def mb_generate_version_header(env, target, project_name, namespace):
    """
    """
    template = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates',
        'version_info.h')
    hash = subprocess.check_output(
            ['git', 'log', '-1', '--format=%H', 'HEAD'],
            shell=sys.platform.startswith('win')).strip()
    status = subprocess.check_output(
            ['git', 'status', '--porcelain', '--ignored'],
            shell=sys.platform.startswith('win'))
    modified = re.search('^\s?[MADRCU]+\s+(.*)$', status, re.MULTILINE)
    context = {
        'project': project_name.upper(),
        'namespace': namespace,
        'major': env.MBVersionMajor(),
        'minor': env.MBVersionMinor(),
        'point': env.MBVersionPoint(),
        'build': env.MBVersionBuild(),
        'hash': hash,
        'modified': 'true' if (modified is not None) else 'false'
    }
    return env.SimpleMustacheCodegen(target, template, context)


def generate(env):
    env.Tool('options')
    env.Tool('mustache_codegen')

    load_version(env)

    env.AddMethod(mb_version, 'MBVersion')
    env.AddMethod(mb_version_major, 'MBVersionMajor')
    env.AddMethod(mb_version_minor, 'MBVersionMinor')
    env.AddMethod(mb_version_point, 'MBVersionPoint')
    env.AddMethod(mb_version_build, 'MBVersionBuild')

    env.AddMethod(mb_generate_version_header, 'MBGenerateVersionHeader')

def exists(env) :
    return True
