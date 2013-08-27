
# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--no-variant',
        dest='no_variant',
        action='store_true',
        help='Turns off the variant dir if it would be used. Mainly for use with IDEs. '
                'Note that for python projects and on windows this is on by default.')

def mb_sconscript(env, sconscript, python_project = False):
    if python_project or env.MBIsWindows() or env.MBGetOption('no_variant'):
        env.SConscript(sconscript)
    else:
        env.SConscript(sconscript, variant_dir='obj/', duplicate=1)

def generate(env):
    tool_exists = 'MB_SCONSTRUCT_TOOL_LOADED'
    if env.get(tool_exists, False):
        print 'tool "mb_sconstruct" being loaded multiple times'
    else:
        env[tool_exists] = True

    env.Tool('options')
    env.Tool('common')

    common_arguments(env)

    env.AddMethod(mb_sconscript, 'MBSConscript')

def exists(env) :
    return True