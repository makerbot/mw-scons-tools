# Copyright 2013 MakerBot Industries

import os
import re

def mb_generate_version_resource(env,
                                 outfile,
                                 file_description,
                                 internal_name,
                                 original_filename,
                                 product_name):
    template_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates',
        'version.rc')

    # create the distribution file from a template
    with open(template_file, 'r') as version_template:
        version_text = version_template.read()
        version_text = version_text.decode('utf-16')

        subst = {
            'major': env.MBVersionMajor(),
            'minor': env.MBVersionMinor(),
            'point': env.MBVersionPoint(),
            'build': env.MBVersionBuild(),
            'file_description': file_description,
            'internal_name': internal_name,
            'original_filename': original_filename,
            'product_name': product_name
        }
        version_text = version_text % subst

    with open(outfile, 'w') as ver_file:
        ver_file.write(version_text)

    return env.File(outfile)

def generate(env):
    env.AddMethod(mb_generate_version_resource, 'MBGenerateVersionResource')

def exists(env):
    return True
