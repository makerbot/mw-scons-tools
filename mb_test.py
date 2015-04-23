"""
Tools for running things that you just built from SCons.
"""

import SCons.Node.Alias


# We want scons to treat our unit tests as actual scons nodes, but a
# unit test does not produce any output on the filesystem.  The only
# built-in scons node class that does not need to be tied to a fixed
# filesystem location is an Alias, but an Alias has its build method
# specifically disabled for some reason.
class TestNode(SCons.Node.Alias.Alias):
    build = SCons.Node.Node.build


def _get_ld_path_key(env):
    if env.MBIsWindows():
        key = 'PATH'
    elif env.MBIsMac():
        key = 'DYLD_LIBRARY_PATH'
    else:
        key = 'LD_LIBRARY_PATH'
    return key


def mb_prepend_dl_path(env, path):
    key = _get_ld_path_key(env)
    env.PrependENVPath(key, path)


def mb_append_dl_path(env, path):
    key = _get_ld_path_key(env)
    env.AppendENVPath(key, path)


def set_test_paths(env):
    if env.MBIsMac():
        # When we are installing on mac, all libraries and binaries
        # have the framework library paths hard coded in place in the
        # obj directory, so we have no access to the developer linked
        # binaries for running unit tests.
        env.Tool('mb_install')
        env.PrependENVPath('DYLD_ROOT_PATH', env.MBGetOption('install_prefix'))
    if env.MBIsWindows():
        # I don't think that we should be relying on our builders
        # having all third party libraries on the system path.
        env.AppendENVPath('PATH', env['MB_BIN_DIR'])


def mb_add_always_run_test(env, action, deps=(), **kwargs):
    """
    Add a test that will always be run when the "test" target is
    selected.  You can specify targets that must be built before
    the test is run with deps, but the test will still run even
    if no dependency has changed.
    """
    # So when the test fails, the only context that scons provides
    # immediately after the failure is the node name we are building,
    # so we want the node name to indicate the action that failed.
    if isinstance(action, str):
        name = action
    else:
        name = getattr(action, '__name__', 'test')
    test = TestNode(name)
    env.Command(test, deps, action, **kwargs)
    env.Alias('test', test)
    env.AlwaysBuild(test)


def generate(env):
    env.Tool('common')
    if 'mb_install' not in env['TOOLS']:
        env.Tool('mb_install')

    env.AddMethod(mb_prepend_dl_path, 'MBPrependDLPath')
    env.AddMethod(mb_append_dl_path, 'MBAppendDLPath')

    env.AddMethod(mb_add_always_run_test, 'MBAddAlwaysRunTest')

    set_test_paths(env)


def exists(env):
    return True
