import os
import re
env = Environment(
    ENV=os.environ,
    tools=['default', 'mb_install'],
    toolpath=['#/'])
# do not install any file that matches
# any of these patterns
excludes = [
    '(^.*\.git(/.*)?$)',
    '(^.*debian(/.*)?$)',
    '(^.*obj/(.*)$)',
    '(^.*\.pyc$)',
    '(^.*\.gitignore$)']
exclude_pat = '|'.join(excludes)
exclude_re = re.compile(exclude_pat)

things_to_install  = [elem for elem in
    env.MBRecursiveFileGlob('.', '*')
    if None is exclude_re.match(elem.srcnode().path)]
for elem in things_to_install:
    # install scons tools to fake_root/scons
    Default(elem)
    src_path = elem.srcnode().path
    dest_path = os.path.join(
        'scons',
        src_path)
    env.MBInstallSystem(elem, dest_path)

env.MBCreateInstallTarget()
