# SCons condensed readme

This document is supposed to act as a minimal guide to how we should use SCons, so you don't have to read the entire ----ing manual.

The entire ----ing manual can be found [here](http://www.scons.org/doc/HTML/scons-man.html)

## Basic concepts

Scons reads through your SConstruct & Sconscripts and builds a dependency tree before it actually tries to create anything. In general, when writing your own build steps, do the scons-y thing and make sure the work is done at dependency tree execution (not creation) time.

When calling a top-level SCons function like Action or Builder anything you expect the environment to expand will be expanded when that Action or Builder is actually called. If you call env.Action or env.Builder, variable expansion happens immediately.

###

## Basic Components

### Builders

Full docs [here](http://www.scons.org/doc/HTML/scons-man.html#lbAH), [here](http://www.scons.org/doc/HTML/scons-man.html#lbAP), and [here (v2.3.0)](http://www.scons.org/doc/2.3.0/HTML/scons-user/c3621.html)

Builders are basically compile steps. They take a source and produce a target. A builder has an 'action' associated with it that should do all the work of producing the target. The action will happen only if scons decides it's needed to resolve a dependency.

Builders can also be passes custom environment overrides, so if you build three different binaries in a SConscript there's no need for three different Environments, or cloning your environment multiple times.

*Custom Builders*

can be made in a few ways

    def build_func(target, source, env):
        # Code to create target from source
        if success:
            return 0 or None
        else:
            return a string or raise an exception
    b = Builder(action=build_func)

or

    # This will create the action at sconscript evaluation time
    b = Builder(action='<external command> $ENV_VARIABLE $SOURCE ${TARGET.file}')

or

    # This will create the action at dependency tree execution time
    def generator_func(target, source, env, for_signature):
        return '<external command> {} {} {}'.format(env.variable, source[0], target.abspath)
    b = Builder(generator=generator_func)

and added to the environment like:

    env.Append(BUILDERS={'BuilderName': b})

*Emitters*

modifies the targets and sources based on the environment

    def emmitter_func(target, source, env):
        # Code to change target or source lists or build new lists
        return target, source

### Methods

Methods are just python functions that are added to an environment using env.AddMethod

Mostly they're good for grouping calls to builders or the construction environment

    method_func(env, other arguments...):
        # Modify env
        # and/or
        # Call some builders
    env.AddMethod(method_func, 'MethodFunc')

    env.MethodFunc(other arguments...)


### Actions

Full docs [here](http://www.scons.org/doc/HTML/scons-man.html#lbAQ)

Actions represent a thing to be done.

The type of object passed to action determines how the action is created. Notably,

    Action(['g++', '$TARGET', '$SOURCE'])

would actually try to create three actions, one for each element in the list, while

    Action([['g++', '$TARGET', '$SOURCE']])

or

    Action('g++ $TARGET $SOURCE')

would do the right thing.


## Questions to be determined experimentally

### non-file dependencies

I know that you can use 'something_fake' as a target and assuming it doesn't actually get built, that dependency will be unsatisfied when it comes to building '.' (building everything), but can you say

    def add_flags(target, source, env):
        env.Append(FLAG=source)
    b = env.Builder(action=add_flags)
    env.Append(BUILDERS={'AddFlags': b})

    flags = env.AddFlags('special_flags', ['flagA', 'flagB'])
    prog = env.Program('program', sources)
    env.Depends(prog, flags)

This might be a good way to make the windows builder depend on flags passed to it? Or there might be a better way.



