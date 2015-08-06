import SCons.Util
import os
import sys
import shutil

sys.path.append(os.path.dirname(__file__))
from addDependentLibsToBundle import addDependentLibsToBundle

resource_dir = 'Contents/Resources'
framework_dir = 'Contents/Frameworks'
mac_dir = 'Contents/MacOS'
plugin_dir = 'Contents/plugins'
plist_file = 'Contents/Info.plist'


def createBundle(target, source, env):
    bundle_dir = env['BUNDLE_DIR']
    print "creating bundle at " + bundle_dir
    if os.path.isdir(bundle_dir):
        shutil.rmtree(bundle_dir)
    os.makedirs(os.path.join(bundle_dir, resource_dir))
    os.makedirs(os.path.join(bundle_dir, framework_dir))
    os.makedirs(os.path.join(bundle_dir, mac_dir))
    if env['BUNDLE_PLUGINS']:
        os.mkdir(os.path.join(bundle_dir, plugin_dir))
    # add binaries
    for bin in env.Flatten(env['BUNDLE_BINARIES']):
        shutil.copy(str(bin), os.path.join(bundle_dir, mac_dir))
    for bin in env.Flatten(env['BUNDLE_PLUGINS']):
        shutil.copy(str(bin), os.path.join(bundle_dir, plugin_dir))
    # add resources
    for resdir in env['BUNDLE_RESOURCEDIRS']:
        # TODO act sensitive to resdir being a scons target.
        # for now assuming a string since we don't use it
        shutil.copytree(str(resdir), os.path.join(bundle_dir, resource_dir))
    # write Info.plist -- TODO actually write it not copy it
    plistFile = env['BUNDLE_PLIST']
    shutil.copy(str(plistFile), os.path.join(bundle_dir, plist_file))
    # add icon -- TODO generate .icns file from png or svg
    iconFile = env['BUNDLE_ICON']
    shutil.copy(str(iconFile), os.path.join(bundle_dir, resource_dir))
    # add dependent libraries, fixing all absolute paths
    if 'BUNDLE_DEPENDENT_LIBS' in env:
            addDependentLibsToBundle(bundleDir)


def bundleEmitter(target, source, env):
    # Scons needs this builder to emit the complete list of files it creates
    # instead of just the base directory in order to correctly populate the
    # MB_INSTALL_TARGETS and install_manifest.txt
    # TODO this builder takes in a list of dirs as BUNDLE_RESOURCEDIRS
    # so we will need to add some logic to extract all of those files here
    # or find some other work-around if we end up using them.
    # TODO this builder/emitter does nothing with the frameworks
    bundle_dir = os.path.join(os.getcwd(), env['BUNDLE_NAME']+".app")
    env['BUNDLE_DIR'] = bundle_dir
    for bin in env.Flatten(env['BUNDLE_BINARIES']):
        target.append(env.File(os.path.join(bundle_dir, mac_dir, str(bin))))
    if env['BUNDLE_PLUGINS']:
        for bin in env.Flatten(env['BUNDLE_PUGINS']):
            plugin_path = os.path.join(bundle_dir, plugin_dir, str(bin))
            target.append(env.File(plugin_path))
    target.append(env.File(os.path.join(bundle_dir, plist_file)))
    icon_file = os.path.basename(str(env['BUNDLE_ICON']))
    target.append(env.File(os.path.join(bundle_dir, resource_dir, icon_file)))
    source = env['BUNDLE_BINARIES']
    return target, source


def generate(env):
    Builder = SCons.Builder.Builder
    Action = SCons.Action.Action
    bundleBuilder = Builder(
        action=Action(createBundle),
        emitter=bundleEmitter,
    )
    env['BUNDLE_RESOURCEDIRS'] = []
    env['BUNDLE_PLUGINS'] = []
    env.Append(BUILDERS={'Bundle': bundleBuilder})


def exists(env):
    return True
