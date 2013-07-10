import SCons.Util, os
import sys
sys.path.append( os.path.dirname(__file__) )
from addDependentLibsToBundle import addDependentLibsToBundle

def run(command) :
	print(command)
	return os.system(command)


def createBundle(target, source, env) :
	bundleDir = str(target[0])
	print "creating bundle at " + bundleDir
	run("rm -rf "+bundleDir )
	run("mkdir -p %s/Contents/Resources" % bundleDir )
	run("mkdir -p %s/Contents/Frameworks" % bundleDir )
	run("mkdir -p %s/Contents/MacOS" % bundleDir )
	if env['BUNDLE_PLUGINS'] :
		run("mkdir -p %s/Contents/plugins" % bundleDir )
	# add binaries
	for bin in env.Flatten( env['BUNDLE_BINARIES'] ) :
		run('cp %s %s/Contents/MacOS/' % (str(bin), bundleDir) )
	for bin in env.Flatten( env['BUNDLE_PLUGINS'] ) :
		run('cp %s %s/Contents/plugins/' % (str(bin), bundleDir) )
	# add resources
	for resdir in env['BUNDLE_RESOURCEDIRS'] :
		# TODO act sensitive to resdir being a scons target. now assuming a string
		run('cp -r %s %s/Contents/Resources/' % (str(resdir), bundleDir) )
	# write Info.plist -- TODO actually write it not copy it
	plistFile = env['BUNDLE_PLIST']
	run('cp %s %s/Contents/Info.plist' % (plistFile, bundleDir) )
	# add icon -- TODO generate .icns file from png or svg
	iconFile = env['BUNDLE_ICON']
	run('cp %s %s/Contents/Resources' % (iconFile, bundleDir) )
	# add dependent libraries, fixing all absolute paths
	if 'BUNDLE_DEPENDENT_LIBS' in env:
            addDependentLibsToBundle( bundleDir )
	

def bundleEmitter(target, source, env):
	target = env.Dir(env['BUNDLE_NAME']+".app")
	source = env['BUNDLE_BINARIES']
	return target, source

def generate(env) :
	print "Loading Bundle tool"
	Builder = SCons.Builder.Builder
	Action = SCons.Action.Action
	bundleBuilder = Builder(
		action = Action( createBundle ),
		emitter = bundleEmitter,
	)
	env['BUNDLE_RESOURCEDIRS'] = []
	env['BUNDLE_PLUGINS'] = []
	env.Append( BUILDERS={'Bundle' : bundleBuilder } )

def exists(env) :
	return True
