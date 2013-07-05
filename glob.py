# Copyright 2013 MakerBot Industries

import fnmatch
import os

def RecursiveFileGlob(env, root, pattern):
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

def generate(env):
    env.AddMethod(RecursiveFileGlob, 'RecursiveFileGlob')

def exists(env):
    return True
