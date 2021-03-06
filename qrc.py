# Copyright 2013 MakerBot Industries

import os

def MBGenQRC(target, source, env):
    '''Create an XML QRC file'''
    with open(str(target[0]), 'w') as f:
        f.write('<RCC>\n')
        f.write('  <qresource>\n')
        for s in sorted((str(s) for s in source)):
            path = env.MBStripVariantDir(s)
            path = os.sep.join(path.split(os.sep)[1:])
            f.write('    <{0}>{1}</{0}>\n'.format('file', path))
        f.write('  </qresource>\n')
        f.write('</RCC>\n')

def generate(env):
    env.Tool('mb_sconstruct')

    env.Append(BUILDERS = {'MBGenQRC': env.Builder(action = MBGenQRC)})

def exists(env):
    return True
