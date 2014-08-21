import os
import re

env = Environment(
    ENV=os.environ,
    tools=['default', 'mb_install'],
    toolpath=['#/'])

excludes = [
    '(^.*\.git(/.*)?$)',
    '(^.*debian(/.*)?$)',
    '(^.*obj/(.*)?$)']
exclude_pat = '|'.join(excludes)
exclude_re = re.compile(exclude_pat)

things_to_install  = [elem for elem in
    env.MBRecursiveFileGlob('.', '*')
    if None is exclude_re.match(elem.srcnode().path)]
for elem in things_to_install:
    dest_path = os.path.join(
        'share', 'scons', 'site_scons', 'site_tools',
        elem.srcnode().path)
    print dest_path
    env.MBInstallSystem(elem, dest_path)

env.MBCreateInstallTarget()
