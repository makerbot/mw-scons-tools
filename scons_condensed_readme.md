# SCons condensed readme

This document is supposed to act as a minimal guide to how we should use SCons, so you don't have to read the entire ----ing manual.

The entire ----ing manual can be found in these [two](http://www.scons.org/doc/HTML/scons-man.html) [documents](http://www.scons.org/doc/2.3.0/HTML/scons-user/index.html) (two is better than one, right?)


## Basic concepts

Scons reads through your SConstruct & Sconscripts and builds a dependency tree before it actually tries to create anything. In general, when writing your own build steps, do the scons-y thing and make sure the work is done at dependency tree execution (not creation) time.

When using scons build-in builders, the scons doc says that they are all *potentially* available out of the box. If you find one that throws an error when you try to use it, it may actually be in your scons source tree, just not on the environment. Try grepping around for it. For example, to use the Substfile and Textfile builders you have to specify the 'textfile' tool to actually use them, even though the docs don't mention it.

## Basic Components

### Builders

Full docs [here][Builder Methods], [here][Builder Objects], [here][Command], and [here][Writing Your Own Builders]

Builders are basically compile steps. They take a source and produce a target. A builder has an 'action' associated with it that should do all the work of producing the target. The action will happen only if scons decides it's needed to resolve a dependency.

Builders can also be passed custom environment overrides, so if you build three different binaries in a SConscript there's no need for three different Environments or cloning your environment multiple times.

Example:

    env.Append(CCFLAGS=common_flags)
    env.MBProgram('conveyor', conveyor_sources, LIBS=conveyor_libs)
    env.MBProgram('ping',     ping_sources,     LIBS=ping_libs)

**[Custom Builders][Writing Your Own Builders]**

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

**Emitters**

modifies the targets and sources based on the environment

    def emmitter_func(target, source, env):
        # Code to change target or source lists or build new lists
        return target, source


### Methods

Methods are just python functions that are added to an environment using env.AddMethod

Mostly they're good for grouping calls to builders or modifications to the construction environment

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

### Scanners

Full Docs [here][Scanner Objects] and [here][Writing Scanners]

Scanners look at the contents of files and create dependencies based on the contents. Like seeing that a .cpp has a #include "something.h" and saying "this .cpp depends on somthing.h"

If you're going to mess with these read the full docs for them

## Variable Substitution & Construction Variable Expansion

Full docs [here][Construction Variables], [here][Construction Environments], [here][Variable Substitution], and [here][Python Code Substitution]

Scons supports variable replacement in many strings, especially those representing commands. If you want to manually do substitution on a string, use the [subst] method, which will recursively expand a string, or array access `env['thing']`.

You can use curly braces to separate the variable from other characters, like `${TARGET}_bakup`. You can also access attributes of the thing being replaced like `${THING.member}` or `${LIST[0]}`. In fact, code between ${ and } is run through python eval, so comparisons and ternarys are valid as well.

When calling a top-level SCons function like Action or Builder anything you expect the environment to expand will be expanded when that Action or Builder is actually called. If you call env.Action or env.Builder, variable expansion happens immediately.

### In an Action/Command (Variable Substitution)

Use `$SOURCE`, `$SOURCES`, `$CHANGED_SOURCES`, `$UNCHANGED_SOURCES`, `$TARGET`, `$TARGETS`, `$CHANGED_TARGETS`, and `$UNCHANGED_TARGETS` as appropriate

These variables are reserved and should not be explicitly set. They also have certain attributes you can access, the most useful of which are the obvious things like `file`, `abspath`, and `suffix` as well as things like `srcpath` and `srcdir`, which will give the version of the file in the variant dir. A list of all such attributes is [here][Variable Substitution]

## Non-file Dependencies

Dependencies are handled via nodes in a dependency tree. There are File, Dir, and Value Nodes (maybe others as well?)

Value Nodes let us do dependencies on non-files. In the SConstruct below, whenever the value of val changes, com will be rebuilt

    env = Environment()
    val = env.Value('test')
    com = env.Command('out.txt', 'in.txt', 'type $SOURCE > $TARGET')
    env.Depends(com, val)

## Other

I always find myself looking up this comment in the scons source code. Putting it here for reference.

> The only difference between the Textfile builder and the Substfile builder is that strings are converted to Value() nodes for the former and File() nodes for the latter.  To insert files in the former or strings in the latter, wrap them in a File() or Value(), respectively.

[Action Objects]: http://www.scons.org/doc/HTML/scons-man.html#lbAQ
[Builder Methods]: http://www.scons.org/doc/HTML/scons-man.html#lbAH
[Builder Objects]: http://www.scons.org/doc/HTML/scons-man.html#lbAP
[Writing Your Own Builders]: http://www.scons.org/doc/2.3.0/HTML/scons-user/c3621.html
[Command]: http://www.scons.org/doc/2.3.0/HTML/scons-user/c3895.html
[Construction Environments]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x1444.html
[Construction Variables]: http://www.scons.org/doc/HTML/scons-man.html#lbAK
[Variable Substitution]: http://www.scons.org/doc/HTML/scons-man.html#lbAS
[Python Code Substitution]: http://www.scons.org/doc/HTML/scons-man.html#lbAT
[Execute]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x3095.html
[subst]: http://www.scons.org/doc/2.3.0/HTML/scons-user/x1444.html#AEN1498
[Scanner Objects]: http://www.scons.org/doc/HTML/scons-man.html#lbAU
[Writing Scanners]: http://www.scons.org/doc/2.3.0/HTML/scons-user/c3966.html
