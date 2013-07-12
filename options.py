from SCons.Script import AddOption, GetOption
from optparse import OptionConflictError

'''
Some conventions to keep this sane:
  * function definitions are in lowercase_with_underscores
  * if the function is exported by the tool, it starts with mb_
  * functions/builders are exported in camelcase, including the initial MB
  * functions are added in the same order as they appear in this file
Feel free to change the conventions if you think they're wrong,
just make sure to update everything to match those conventions
'''

# This is pretty silly, but because we load this tool multiple times
# these options can be loaded twice, which raises an error.
# This error can be safely ignored.
def mb_add_option(env, *args, **kwargs):
    try:
        return AddOption(*args, **kwargs)
    except OptionConflictError:
        pass

# This is even sillier -- it's just so that we don't have to import
# GetOption in the other scripts
def mb_get_option(env, *args, **kwargs):
    return GetOption(*args, **kwargs)

def generate(env):
    env.AddMethod(mb_add_option, 'MBAddOption')
    env.AddMethod(mb_get_option, 'MBGetOption')

def exists(env) :
    return True