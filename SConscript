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

# this is only necessary for linux
if env.MBIsLinux():
    things_to_install  = [elem for elem in
        env.MBRecursiveFileGlob('.', '*')
        if None is exclude_re.match(elem.srcnode().path)]
    for elem in things_to_install:
        # This code assumes that the system prefix is /usr
        # Scons looks for tools in /usr/share/site_scons/site_tools
        Default(elem)
        src_path = elem.srcnode().path
        dest_path = os.path.join(
            'share', 'scons', 'site_scons', 'site_tools',
            src_path)
        env.MBInstallSystem(elem, dest_path)
else:
    Default(None)

env.MBCreateInstallTarget()
