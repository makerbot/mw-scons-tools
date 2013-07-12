
_error = 'error'
_warning = 'warning'
_spam = 'spam'

# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--log-level',
        dest='log_level',
        metavar='LEVEL',
        type='string',
        action='store',
        default=_warning,
        help='Sets the MakerBot log level to [' +
            _error + '|' +
            _warning + '|' +
            _spam + ']')

def log_level_at_least(env, level):
    log_level = env.MBGetOption('log_level')
    log_level = log_level.lower()
    if _spam == log_level:
        return True
    elif _error == level:
        return True
    elif level == log_level:
        return True
    else:
        return False

# Should this raise an error or something?
def mb_log_error(env, message):
    if log_level_at_least(env, _error):
        print message

def mb_log_warning(env, message):
    if log_level_at_least(env, _warning):
        print message

def mb_log_spam(env, message):
    if log_level_at_least(env, _spam):
        print message

def generate(env):
    env.Tool('options')

    common_arguments(env)

    env.AddMethod(mb_log_error, 'MBLogError')
    env.AddMethod(mb_log_warning, 'MBLogWarning')
    env.AddMethod(mb_log_spam, 'MBLogSpam')


def exists(env) :
    return True