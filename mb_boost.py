#from SCons.Script import ARGUMENTS
#from SCons.FS import Dir
import sys, os
import re

_is_windows = ('win32' == sys.platform)
_is_linux = (sys.platform.startswith('linux'))
_is_mac = ('darwin' == sys.platform)

def mb_is_windows(env):
  return _is_windows

def mb_is_linux(env):
  return _is_linux

def mb_is_mac(env):
  return _is_mac

def mb_prepare_boost(env):
    boost_dir = env['MB_BOOST_DIR']
    include_dir = os.path.join(boost_dir, 'include')
    boost_version_re = re.compile('^boost-(?P<major>\d+)_(?P<minor>\d+)$')
    versions = [(int(match.group('major')), int(match.group('minor')))
            for match in (boost_version_re.match(a) 
            for a in os.listdir(include_dir)) if match]
    subdir = 'boost-{}_{}'.format(*(versions.sorted()[-1])
    include = os.path.join(include_dir, subdir)
    lib = os.path.join(boost_dir, 'lib')
    vars = {'CPPPATH': include, 'LIBPATH', lib}
    print include
    print lib
    env.Append(vars)

def generate(env):
    print "Loading MakerBot boost tool"
    if mb_is_windows(env):
        mb_prepare_boost(env)
    

def exists(env) :
	return True
