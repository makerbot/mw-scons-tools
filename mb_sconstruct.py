
import re

NO_VARIANT = 'no_variant'

# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--no-variant',
        dest=NO_VARIANT,
        action='store_true',
        help='Turns off the variant dir if it would be used. Mainly for use with IDEs. '
                'Note that for python projects and on windows this is on by default.')

def mb_use_variant_dir(env):
    return (not env.MBIsWindows() and not env.MBGetOption(NO_VARIANT))

def mb_variant_dir(env):
    if env.MBUseVariantDir():
        return 'obj'
    else:
        return ''

def mb_strip_variant_dir(env, path):
    ''' If path starts with the variant dir, remove the dir '''
    return re.sub('^(\\\\|/)*' + env.MBVariantDir() + '(\\\\|/)*', '', path)

def mb_sconscript(env, sconscript, python_project = False):
    if python_project or not env.MBUseVariantDir():
        env.SConscript(sconscript)
    else:
        env.SConscript(sconscript, variant_dir=env.MBVariantDir(), duplicate=1)

def generate(env):
    env.Tool('options')
    env.Tool('common')
    env.Tool('version')

    common_arguments(env)

    env.AddMethod(mb_use_variant_dir, 'MBUseVariantDir')
    env.AddMethod(mb_variant_dir, 'MBVariantDir')
    env.AddMethod(mb_strip_variant_dir, 'MBStripVariantDir')
    env.AddMethod(mb_sconscript, 'MBSConscript')

def exists(env) :
    return True
