# Copyright 2013 MakerBot Industries

import os
import re

def mb_generate_version_resource(env, outfile):
    version_regex = re.compile('(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<point>[0-9]+)')

    try:
        version = version_regex.match(env.MBVersion())
    except Exception as e:
        raise Exception("could not parse version number")

    template_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates',
        'version.rc')

    # create the distribution file from a template
    with open(template_file, 'r') as version_template:
        version_text = version_template.read()
        version_text = version_text.decode('utf-16')

        subst = {
            'major': version.group('major'),
            'minor': version.group('minor'),
            'point': version.group('point'),
            'build': env.MBBuildNumber(),
            'file_description': "TODO",
            'internal_name': "TODO",
            'original_filename': "TODO",
            'product_name': "TODO"
        }
        version_text = version_text % subst

    with open(outfile, 'w') as ver_file:
        ver_file.write(version_text)

    return env.File(outfile)

def generate(env):
    env.AddMethod(mb_generate_version_resource, 'MBGenerateVersionResource')

def exists(env):
    return True
