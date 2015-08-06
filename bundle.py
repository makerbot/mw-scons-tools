import SCons.Util, os
import sys

sys.path.append( os.path.dirname(__file__) )
from addDependentLibsToBundle import addDependentLibsToBundle

def run(command) :
	print(command)
	return os.system(command)


def createBundle(target, source, env) :
    bundleDir = env['BUNDLE_DIR']
    print "creating bundle at " + bundleDir
    run("rm -rf '%s'" % bundleDir )
    run("mkdir -p '%s/Contents/Resources'" % bundleDir )
    run("mkdir -p '%s/Contents/Frameworks'" % bundleDir )
    run("mkdir -p '%s/Contents/MacOS'" % bundleDir )
    if env['BUNDLE_PLUGINS'] :
        run("mkdir -p '%s/Contents/plugins'" % bundleDir )
    # add binaries
    for bin in env.Flatten( env['BUNDLE_BINARIES'] ) :
        run("cp '%s' '%s/Contents/MacOS/'" % (str(bin), bundleDir) )
    for bin in env.Flatten( env['BUNDLE_PLUGINS'] ) :
        run("cp '%s' '%s/Contents/plugins/'" % (str(bin), bundleDir) )
    # add resources
    for resdir in env['BUNDLE_RESOURCEDIRS'] :
        # TODO act sensitive to resdir being a scons target. now assuming a string
        run("cp -r '%s' '%s/Contents/Resources/'" % (str(resdir), bundleDir) )
    # write Info.plist -- TODO actually write it not copy it
    plistFile = env['BUNDLE_PLIST']
    run("cp '%s' '%s/Contents/Info.plist'" % (plistFile, bundleDir) )
    # add icon -- TODO generate .icns file from png or svg
    iconFile = env['BUNDLE_ICON']
    run("cp '%s' '%s/Contents/Resources'" % (iconFile, bundleDir) )
    # add dependent libraries, fixing all absolute paths
    if 'BUNDLE_DEPENDENT_LIBS' in env:
            addDependentLibsToBundle( bundleDir )
	

def bundleEmitter(target, source, env):
    # Scons needs this builder to emit the complete list of files it creates
    # instead of just the base directory in order to correctly populate the
    # MB_INSTALL_TARGETS and install_manifest.txt
    # TODO this builder takes in a list of dirs as BUNDLE_RESOURCEDIRS
    # so we will need to add some logic to extract all of those files here
    # or find some other work-around if we end up using them.
    # TODO this builder/emitter does nothing with the frameworks
    bundleDir = os.path.join(os.getcwd(), env['BUNDLE_NAME']+".app")
    env['BUNDLE_DIR'] = bundleDir
    resourceDir = bundleDir+'/Contents/Resources/'
    macDir = bundleDir+'/Contents/MacOS/'
    pluginDir = bundleDir+'/Contents/plugins/'
    for bin in env.Flatten(env['BUNDLE_BINARIES']):
        target.append(env.File(macDir+str(bin)))
    if env['BUNDLE_PLUGINS']:
        for bin in env.Flatten(env['BUNDLE_PUGINS']):
            target.append(env.File(pluginDir + str(bin)))
    target.append(env.File(bundleDir+"/Contents/Info.plist"))
    target.append(env.File(resourceDir + os.path.basename(str(env['BUNDLE_ICON']))))
    source = env['BUNDLE_BINARIES']
    return target, source

def generate(env) :
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
