# Copyright 2013 MakerBot Industries

import os
import string

import SCons

CURRENT_FILE = os.path.abspath(__file__)
if CURRENT_FILE.endswith('.pyc'):
      CURRENT_FILE = CURRENT_FILE[:-1]

def _gen_version_resource_action(env, target, source):
    """SCons action for creating a version resource

    Takes a template version resource and fills in the values.  target should
    be the file to write to, source should be a SCons Node containing a dict
    of substitutions to be made.
    """
    template_file = os.path.join(
        os.path.dirname(CURRENT_FILE),
        'templates',
        'version.rc')

    # create the distribution file from a template
    with open(template_file, 'r') as version_template:
        version_text = version_template.read()

    version_text = version_text.decode('utf-16')
    text_template = string.Template(version_text)
    version_text = text_template.substitute(source[0].read())

    with open(target[0].abspath, 'w') as ver_file:
        ver_file.write(version_text)

    # Success
    return 0

def _gen_version_resource_method(env,
                                 target,
                                 file_description,
                                 internal_name,
                                 original_filename,
                                 product_name):
    """Provides a nice wrapper around the version resource action

    Correctly sets up dependencies and provides argument names to enforce all
    the arguments being specified.

    """
    substitutions = {
        'major': env.MBVersionMajor(),
        'minor': env.MBVersionMinor(),
        'point': env.MBVersionPoint(),
        'build': env.MBVersionBuild(),
        'file_description': file_description,
        'internal_name': internal_name,
        'original_filename': original_filename,
        'product_name': product_name
    }

    substitutions = SCons.Node.Python.Value(substitutions)

    rc = env._gen_version_resource(
        target + '_version.rc',
        substitutions)

    # Pick up any changes to this file that might not be seen by scons
    # This isn't normally necessary for a final product build system,
    # but when it's under development...
    env.Depends(rc, env.File(CURRENT_FILE))

    return rc

def generate(env):
    _gen_version_resource = SCons.Builder.Builder(
        action=SCons.Action.Action(
            _gen_version_resource_action,
            "Creating version rc: '$TARGET'"),
        source_factory=SCons.Node.Python.Value)

    env.Append(BUILDERS={'_gen_version_resource': _gen_version_resource})

    env.AddMethod(_gen_version_resource_method, 'MBGenerateVersionResource')

def exists(env):
    return True
