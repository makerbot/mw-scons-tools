# SCons condensed readme

This document is supposed to act as a minimal guide to how we should use SCons, so you don't have to read the entire ----ing manual.

The entire ----ing manual can be found in these [two](http://www.scons.org/doc/HTML/scons-man.html) [documents](http://www.scons.org/doc/2.3.0/HTML/scons-user/index.html) (two is better than one, right?)


## Basic concepts

Scons reads through your SConstruct & Sconscripts and builds a dependency tree before it actually tries to create anything. In general, when writing your own build steps, do the scons-y thing and make sure the work is done at dependency tree execution (not creation) time.


## Basic Components

### Builders

Full docs [here][Builder Methods], [here][Builder Objects], and [here (v2.3.0)][Writing Your Own Builders]

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

Full docs [here][Action Objects]

Actions represent a thing to be done. They can be made to happen at dependency tree building time with the [Execute] function or delayed to dependency tree execution time by wrapping them in a Builder.

The type of object passed to action determines how the action is created. Notably,

    Action(['g++', '$TARGET', '$SOURCE'])

would actually try to create three actions, one for each element in the list, while

    Action([['g++', '$TARGET', '$SOURCE']])

or

    Action('g++ $TARGET $SOURCE')

would do the right thing.

Also, when creating an object you can specify that it can execute a batch of files at once, e.g. compiling multiple .c files in a single call. If you do that use `$CHANGED_SOURCES` instead of `$SOURCES` and `$CHANGED_TARGETS` instead of `$TARGETS`


## Variable Substitution & Construction Variable Expansion

Full docs [here][Construction Variables], [here][Construction Environments], [here][Variable Substitution]

Scons supports variable replacement in many strings, especially those representing commands.

If you want to manually do substitution on a string, use the [`subst`] method

When calling a top-level SCons function like Action or Builder anything you expect the environment to expand will be expanded when that Action or Builder is actually called. If you call env.Action or env.Builder, variable expansion happens immediately.

### In an Action

Use `$SOURCE`, `$SOURCES`, `$CHANGED_SOURCES`, `$UNCHANGED_SOURCES`, `$TARGET`, `$TARGETS`, `$CHANGED_TARGETS`, and `$UNCHANGED_TARGETS` as appropriate

You can

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

[Action Objects]: http://www.scons.org/doc/HTML/scons-man.html#lbAQ
[Builder Methods]: http://www.scons.org/doc/HTML/scons-man.html#lbAH
[Builder Objects]: http://www.scons.org/doc/HTML/scons-man.html#lbAP
[Writing Your Own Builders]: http://www.scons.org/doc/2.3.0/HTML/scons-user/c3621.html
[Construction Environments]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x1444.html
[Construction Variables]: http://www.scons.org/doc/HTML/scons-man.html#lbAK
[Variable Substitution]: http://www.scons.org/doc/HTML/scons-man.html#lbAQ
[Execute]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x3095.html
[subst]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x1444.html#AEN1498
