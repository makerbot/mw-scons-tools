# Copyright 2013 MakerBot Industries

import os
import string
import random

import SCons

# environment keys
DEFAULT_PLATFORM_BITNESS = 'x64'
MB_WINDOWS_PLATFORM_BITNESS = 'MB_WINDOWS_PLATFORM_BITNESS'

MB_WINDOWS_CONFIGURATION_TYPE = 'MB_WINDOWS_CONFIGURATION_TYPE'
MB_WINDOWS_PROJECT_NAME = 'MB_WINDOWS_PROJECT_NAME'

DEFAULT_USE_SDL_CHECK = True
MB_WINDOWS_USE_SDL_CHECK = 'MB_WINDOWS_USE_SDL_CHECK'

MB_WINDOWS_IGNORED_LIBS = 'MB_WINDOWS_IGNORED_LIBS'

MB_WINDOWS_DISABLED_WARNINGS = 'MB_WINDOWS_DISABLED_WARNINGS'

MB_WINDOWS_IS_WINDOWED_APPLICATION = 'MB_WINDOWS_IS_WINDOWED_APPLICATION'

MB_WINDOWS_API_IMPORTS = 'MB_WINDOWS_API_IMPORTS'
MB_WINDOWS_API_EXPORT = 'MB_WINDOWS_API_EXPORT'

MB_WINDOWS_STANDARD_CONFIG_DEFINES = 'MB_WINDOWS_STANDARD_CONFIG_DEFINES'

DLL_IMPORT = '__declspec(dllimport)'
DLL_EXPORT = '__declspec(dllexport)'

# these function as both an enumeration and
# constant strings for each configuration type
APPLICATION_TYPE = {'extension': 'exe', 'project_string': 'Application'}
STATIC_LIB_TYPE =  {'extension': 'lib', 'project_string': 'StaticLibrary'}
DYNAMIC_LIB_TYPE = {'extension': 'dll', 'project_string': 'DynamicLibrary'}

DRIVER_SUFFIX = '_lib_srt'

CURRENT_FILE = os.path.abspath(__file__)
if CURRENT_FILE.endswith('.pyc'):
      CURRENT_FILE = CURRENT_FILE[:-1]

TEMPLATE_DIR = os.path.join(
    os.path.dirname(CURRENT_FILE),
    'templates')

def mb_add_windows_devel_lib_path(env, path, platform = None):
    ''' Adds dependecies on other projects' output '''
    if None == platform:
        platform = env.MBWindowsBitness()
    env.Prepend(LIBPATH = [str(env.Dir(os.path.join(path, platform)))])

def mb_set_windows_project_name(env, name):
    ''' Lots of things need a base name for the project '''
    env[MB_WINDOWS_PROJECT_NAME] = name

def mb_windows_add_standard_configuration_preprocessor_define(env, define):
    ''' Add a c preprocessor define that will only
        be used in the driver configuration '''
    env.Append(**{MB_WINDOWS_STANDARD_CONFIG_DEFINES : [define]})

def mb_windows_add_api_import(env, api_import):
    ''' Add an API define that is used in code this project depends on '''
    env.Append(**{MB_WINDOWS_API_IMPORTS : [api_import]})

def mb_windows_set_api_export(env, api_export):
    ''' Set the API define that this project uses to export symbols to a dll '''
    env[MB_WINDOWS_API_EXPORT] = api_export

def mb_windows_set_default_api_export(env, api_export):
    ''' Set the API define that this project uses to export symbols to a dll
        UNLESS it's already set. '''
    if env[MB_WINDOWS_API_EXPORT] == '':
        env[MB_WINDOWS_API_EXPORT] = api_export

def mb_set_windows_use_sdl_check(env, use_sdl):
    ''' turn on/off the use of SDL checks '''
    env[MB_WINDOWS_USE_SDL_CHECK] = use_sdl

def mb_add_windows_ignored_lib(env, lib):
    ''' Some projects use sneaky methods of pulling in static libs that we don't
        want to link against. Use this to get around that.'''
    env.Append(**{MB_WINDOWS_IGNORED_LIBS : [lib]})

def mb_set_windows_is_windowed_application(env, is_windowed = True):
    ''' Set whether the --hide-console option should
        have any effect on this project '''
    env[MB_WINDOWS_IS_WINDOWED_APPLICATION] = is_windowed

def _validate_reason_to_disable(reason):
    """
    HEY YOU

    Yeah, I'm talkin' to you.

    Are you trying to avoid typing a valid reason?

    It's less work to write a valid reason than it is to figure out how
    to not give a valid reason.

    Obviously we can't really make sure a reason is valid,
    but we can discourage people from giving garbage.
    """
    reason = reason.strip()
    invalid = (len(reason) < 10) or (len(reason.split()) < 3)
    if invalid:
        raise Exception(''.join([
            'Hey, "',
            reason,
            '" is a terrible explanation of why a warning is being disabled. ',
            'Could you write a fuller explanation?']))

def mb_windows_disable_warning(env, warning, valid_reason_to_disable):
    """
    Adds warning to the list of disabled warnings with a comment containing
    The reason for disabling.
    """
    _validate_reason_to_disable(valid_reason_to_disable)

    env.Append(
        **{MB_WINDOWS_DISABLED_WARNINGS : [(warning, valid_reason_to_disable)]})


def _expand_project_name(project_name, target_type, debug):
    """Set up the project name with our naming convention."""
    expandedname = project_name

    if debug:
        expandedname += 'd'

    if target_type == STATIC_LIB_TYPE:
        expandedname = 'lib' + expandedname

    return expandedname

def _configuration_string(debug):
    """Returns the vcxproj configuration based on debugness of build."""
    return 'Debug' if debug else 'Release'

def _bool_to_string(value):
    """MSBuild uses lowercase boolean strings"""
    return 'true' if value else 'false'

def _desconsify(nodes):
    """Make all the Files and Nodes and Dirs into strings, strip hashtags"""
    result = []
    for node in nodes:
        if isinstance(node, SCons.Node.FS.Base):
            # denode
            result.append(node.get_abspath())
        else:
            # de-hashtag
            if node.startswith('#'):
                node = node[2:]
            result.append(node)
    return result

def _do_substitutions(substitute_in, substitutions):
    """Replaces parts of a string based on a list of key, value tuples.

    substitutions takes a list of tuples containing pairs of
    keys and values.  Each instance in substitute_in of each key will be
    replaced with that key's value.

    """
    key_format = 'REPLACEME:{}'

    # Just used to modify how we find things to replace
    class _XMLTemplate(string.Template):
        delimiter = '#'
        idpattern = key_format.format('[a-zA-Z0-9_]*')

    template = _XMLTemplate(substitute_in)

    # We make the keys a little more noticable in the xml files
    fixed_subs = {}
    for s in substitutions:
        key = key_format.format(s)
        fixed_subs[key] = substitutions[s]

    return template.substitute(fixed_subs)

def _project_configurations(env, debug, bitness, configuration_type):
    """Create 'ProjectConfiguration' xml element for the vcxproj"""
    template_file = os.path.join(TEMPLATE_DIR, 'project_configuration.xml')
    with open(template_file, 'r') as template:
        template_contents = template.read()

    configuration = _configuration_string(debug)

    subst_dict = {
        'configuration': configuration,
        'bitness': bitness
    }
    result = _do_substitutions(
        template_contents,
        subst_dict)

    if configuration_type != APPLICATION_TYPE:
        subst_dict = {
            'configuration': configuration + DRIVER_SUFFIX,
            'bitness': bitness
        }
        result += _do_substitutions(
            template_contents,
            subst_dict)

    return result

def _configuration_groups(env, project_name, debug, configuration_type):
    """
    Create 'PropertyGroup' xml element labeled 'Configuration' for the vcxproj
    """

    template_file = os.path.join(TEMPLATE_DIR, 'configuration_group.xml')
    with open(template_file, 'r') as template:
        template_contents = template.read()

    configuration = _configuration_string(debug)
    target_name = _expand_project_name(project_name, configuration_type, debug)

    subst_dict = {
        'configuration': configuration,
        'configuration_type': configuration_type['project_string'],
        'debug': _bool_to_string(debug),
        'target_name': target_name,
        'is_driver': _bool_to_string(False)
    }
    result = _do_substitutions(
        template_contents,
        subst_dict)

    if configuration_type != APPLICATION_TYPE:
        target_name = _expand_project_name(project_name, STATIC_LIB_TYPE, debug)
        subst_dict = {
            'configuration': configuration + DRIVER_SUFFIX,
            'configuration_type': configuration_type['project_string'],
            'debug': _bool_to_string(debug),
            'target_name': target_name + DRIVER_SUFFIX,
            'is_driver': _bool_to_string(True)
        }
        result += _do_substitutions(
            template_contents,
            subst_dict)

    return result

# Adapted from http://www.scons.org/wiki/FindTargetSources
def _get_sources(target, ignore=None):
    """Takes a SCons target and finds all sources it depends on"""
    if ignore is None:
        ignore = {}
    sources = []
    for item in target:
        if SCons.Util.is_List(item):
            sources += _get_sources(item, ignore)
        else:
            sources += _get_sources(item.children(scan=1), ignore)

            # Values don't have an abspath
            if isinstance(item, SCons.Node.Python.Value):
                continue
            if item.abspath in ignore:
                continue

            abspath = item.abspath
            ignore[abspath] = True
            sources.append(abspath)

    return sources

def _format_list(prefix, stuff, suffix):
    """Takes a potentially sconsy list and turns it into a single string

    prefix/suffix will be added to the beginning and end of each element in the
    list.

    Example:
      > sconsy_list = ['a', File('b'), [Dir('c'), 'd']]
      > _format_list('_', sconsy_list, '_ ')
      '_a_ _b_ _c_ _d_'

    """
    # Desconsify
    result = SCons.Util.flatten(stuff)
    result = _desconsify(result)
    # Add prefix/suffix
    result = ["{}{}{}".format(prefix, x, suffix) for x in result]
    result = ''.join(result)
    return result

def _remove_dlls(env, libs):
    """Takes the list of libs and removes every item ending with '.dll'

    We can't link against dlls and there's probably a .lib in there for
    it anyway.

    Also flattens the list and converts any scons nodes to strings.
    """
    dllless_libs = []
    # For each item in the list, if it's a .dll, discard it.
    for lib in SCons.Util.flatten(libs):
        lib = str(lib)
        if lib.endswith('.dll'):
            continue
        elif lib.endswith('.lib'):
            dllless_libs.append(lib)
        else:
            # manually append '.lib' if it's missing
            dllless_libs.append(lib + '.lib')
    return dllless_libs

def _subsystem(env, configuration_type, hide_console):
    """Create the SubSytem xml element for the vcxproj Link element"""
    if APPLICATION_TYPE == configuration_type:
        return '<SubSystem>{}</SubSystem>'.format(
            'Windows' if hide_console else 'Console')
    else:
        return ''

def _make_guid(project_name, debug, bitness):
    """Creates a predictable guid for a vcxproj based on the given inputs.

    We want to make sure the guids are always the same for each
    project name, debugness, bitness combo.

    The guid produced is in the form {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}

    Don't reuse project names!

    """
    # convert project name to something readable as hex
    fixed_name = ''
    for char in project_name:
        fixed_name += str(ord(char))
    debug = ('D' if debug else '')
    bitness = ('64' if (bitness == 'x64') else '32')
    guid_base = bitness + debug + fixed_name + 'abcdef1234567890abcdef123456789'
    return '{{{}-{}-{}-{}-{}}}'.format(
        guid_base[0:8],
        guid_base[8:12],
        guid_base[12:16],
        guid_base[16:20],
        guid_base[20:32])

def _get_env_substitutions(env):
    """Extract the environment values we care about, and create a subst dict

    This handles most of the formatting of environment variables into the
    substitution dict for the vcxproj generation.

    """
    #
    # also, any strings that affect formatting and the project_confs/conf_groups
    # basically, all inputs that alter what actually gets built
    configuration_type = env[MB_WINDOWS_CONFIGURATION_TYPE]
    debug = env.MBDebugBuild()
    bitness = env.MBWindowsBitness()
    project_name = env[MB_WINDOWS_PROJECT_NAME]
    hide_console = (
        env.MBGetOption('hide_console') and
        env[MB_WINDOWS_IS_WINDOWED_APPLICATION])

    def _substituted_var(var):
        return env.subst(env[var])

    cppdefines = _substituted_var('CPPDEFINES')
    cppdefines = SCons.Defaults.processDefines(cppdefines)
    cpppath = _substituted_var('CPPPATH')
    libs = _substituted_var('LIBS')
    libs = _remove_dlls(env, libs)
    libpath = _substituted_var('LIBPATH')
    ccflags = _substituted_var('CCFLAGS')
    ignored_libs = env[MB_WINDOWS_IGNORED_LIBS]
    standard_config_defines = env[MB_WINDOWS_STANDARD_CONFIG_DEFINES]
    api_imports = env[MB_WINDOWS_API_IMPORTS]
    api_export = env[MB_WINDOWS_API_EXPORT]
    use_sdl_check = env[MB_WINDOWS_USE_SDL_CHECK]
    disabled_warnings = env[MB_WINDOWS_DISABLED_WARNINGS]

    indent_3 = '      '
    indent_4 = '        '
    semi_endl = ';\n'

    project_configurations = _project_configurations(env, debug, bitness, configuration_type)
    configuration_groups = _configuration_groups(env, project_name, debug, configuration_type)
    subsystem = _subsystem(env, configuration_type, hide_console)

    # additional formatting
    cppdefines = _format_list(indent_4, cppdefines, semi_endl)
    cpppath = _format_list(indent_4, cpppath, semi_endl)
    formatted_libpath  = _format_list(indent_4, libpath, semi_endl)
    formatted_libs = _format_list(indent_4, libs, semi_endl)
    ignored_libs = _format_list(indent_4, ignored_libs, semi_endl)
    standard_config_defines = _format_list(indent_4, standard_config_defines, semi_endl)
    # ccflags is a special case because of a bug in msbuild
    ccflags = _format_list('', ccflags, ';')
    # debug_path is a special case because of how the environment is specified
    debug_path  = _format_list('', libpath, ';')
    api_imports = _format_list(
        indent_3,
        api_imports,
        '=$(importSiblings);\n')
    disabled_warnings = _format_list(
        indent_4,
        ['<!--{}-->\n{}{};'.format(warning[1], indent_4, warning[0])
        for warning in disabled_warnings],
        '')

    substitutions = {
        'project_configurations': project_configurations,
        'project_guid': _make_guid(project_name, debug, bitness),
        'root_namespace': project_name,
        'configuration_groups': configuration_groups,
        'mb_is_debug': _bool_to_string(debug),
        'mb_is_release': _bool_to_string(not debug),
        'api_export': api_export,
        'api_imports': api_imports,
        'standard_config_preprocessor_defines': standard_config_defines,
        'debugging_path': debug_path,
        'sdl_check': _bool_to_string(use_sdl_check),
        'buffer_security_check': _bool_to_string(debug),
        'additional_options': ccflags,
        'preprocessor_definitions': cppdefines,
        'additional_include_directories': cpppath,
        'runtime_library_debugness': 'Debug' if debug else '',
        'disable_specific_warnings': disabled_warnings,
        'additional_dependencies': formatted_libs,
        'ignore_specific_default_libraries': ignored_libs,
        'additional_library_directories': formatted_libpath,
        'subsystem': subsystem,
    }

    return substitutions

def _get_source_substitutions(target):
    """Get the c++ files from the target and format them for substitution

    Filters out the headers, sources, and resources from the target's
    dependencies and formats them for addition to the vcxproj.

    """
    # NB: because this is not being called from a builder, it may not pick up
    # any changes to the dependent headers made after the call to MBGenVcxproj
    all_sources = _get_sources(target)

    source_extensions = [".c", ".cxx", ".cpp", ".c++", ".cc"]
    header_extensions = [".h", ".hxx", ".hpp", ".hh"]
    resource_extensions = [".rc"]

    def _filter_ext(sources, extensions):
        result = []
        for source in sources:
            for extension in extensions:
                if source.lower().endswith(extension.lower()):
                    result.append(source)
                    break
        return result

    formatted_sources = _format_list(
        '    <ClCompile Include="',
        _filter_ext(all_sources, source_extensions),
        '" />\n')
    formatted_headers = _format_list(
        '    <ClInclude Include="',
        _filter_ext(all_sources, header_extensions),
        '" />\n')
    formatted_resources = _format_list(
        '    <ResourceCompile Include="',
        _filter_ext(all_sources, resource_extensions),
        '" />\n')

    substitutions = {
        'cl_compile': formatted_sources,
        'cl_include': formatted_headers,
        'resource_compile': formatted_resources
    }

    return substitutions

def _fill_vcxproj_template(target_file, substitutions):
    """Load the vcxproj template, fill in the substitutions, and write it out"""
    template_file = os.path.join(TEMPLATE_DIR, 'vcxproj.xml')

    # load the template
    with open(template_file, "r") as source:
        source_contents = source.read()

    target_contents = _do_substitutions(source_contents, substitutions)

    # write the file
    with open(target_file, "w") as target:
        target.write(target_contents)
        # This solves the following problem:
        #
        # We know that we're going to be running msbuild on this vcxproj,
        # but the MBRunMSBuild Method can't access the headers that the
        # sources listed in this file depend on.  In fact, MBRunMSBuild
        # should be run whenever this is rebuilt, but it's hard for us to
        # pass that information from one builder to another.  Instead we
        # add this here random number, so that each time this rebuilds it
        # makes MBRunMSBuild run, too.
        target.write(
            '<!--This random value ensures that'
            ' msbuild will be run on this file-->\n')
        target.write('<!--{}-->\n'.format(random.random()))

def _gen_vcxproj_emitter(env, target, source):
    """SCons emitter for the vcxproj builder

    This emitter also messes with the env, which I think emitters are not
    supposed to do, but this seems cleaner than any other means of setting up
    the dependency on the environment variables.  The other options that I
    considered:
    * Using the varlist argument to the Action constructor.
        This would require that we keep a thorough list of all environment
        variables used.  Many of the variables are currently accessed through
        other functions with complicated logic, so it would be quite difficult
        to keep track of all those programatically or manually.
    * Setting dependencies in the action function.
        Does not work.
    * Calculating the substitutions, but not stashing them in the environment.
        Seems unnecessarily computationally intensive.

    """
    vcxproj = str(target[0])
    vcxproj += ('_32' if env.MBWindowsIs32Bit() else '_64')
    vcxproj += ('d' if env.MBDebugBuild() else '')
    vcxproj += '.vcxproj'
    target = [env.File(vcxproj)]

    # Get the environment-based substitutions
    substitutions = _get_env_substitutions(env)
    env['ENV_SUBSTITUTIONS'] = substitutions
    substitution_dependency = SCons.Node.Python.Value(substitutions)
    env.Depends(target, substitution_dependency)

    return target, source

def _gen_vcxproj_action(target, source, env):
    """A SCons action function for a Builder that creates a vcxproj file.

    """
    substitutions = env['ENV_SUBSTITUTIONS']
    # Get the source-based substitutions separately, because the
    # target is not set up quite right until after the emitter has finished
    # TODO(ted): could I just pass the list of sources to _find_headers and move
    # this into the emitter?
    substitutions.update(_get_source_substitutions(target))

    _fill_vcxproj_template(target[0].abspath, substitutions)

    # Success
    return 0

def _run_msbuild_method(env, target, source):
    """A SCons Method function which runs msbuild on a target.

    If any vcxproj properties are passed via the command line,
    they will be passed to msbuild.

    """
    properties = env.MBVcxprojProperties()

    command = [
        'msbuild',
        '/p:Configuration=' + _configuration_string(env.MBDebugBuild()),
        '/p:Platform=' + env.MBWindowsBitness()
    ]
    command += ['/p:{}={}'.format(key, value) for key, value in properties]

    command += ['$SOURCE']

    result = env.Command(target, source, ' '.join(command))

    return result

def _get_windows_binary_target(env):
    """Creates a SCons target for what we expect MSBuild to produce

    Actually, only lists the things we care about installing, but if we wanted
    we could add pdbs and stuff like that to debug builds.

    """
    configuration_type = env[MB_WINDOWS_CONFIGURATION_TYPE]

    project_name = _expand_project_name(
        env[MB_WINDOWS_PROJECT_NAME],
        configuration_type,
        env.MBDebugBuild())
    expandedname = os.path.join('obj', env.MBWindowsBitness(), project_name)

    target = [env.File(expandedname + '.' + configuration_type['extension'])]

    # For .dlls on windows we actually link against
    # the .lib that's generated, so return that, too
    if configuration_type == DYNAMIC_LIB_TYPE:
        target += [env.File(expandedname + '.lib')]

    return target

def _windows_binary(env, target, source):
    """Sets up Builders & dependencies on windows for compiling a binary

    The type of binary is set by MB_WINDOWS_CONFIGURATION_TYPE.

    This creates a .vcxproj and a .rc file to build from.

    """
    env.MBSetWindowsProjectName(target)

    # TODO(ted): we can probably make this only regenerate if the version changes
    # TODO(ted): this path is kind of a hack, will probably cause trouble when something changes
    version_rc = env.MBGenerateVersionResource(
        target + '_version.rc',
        file_description = 'MakerBot Software',
        internal_name = target,
        original_filename = target,
        product_name = target)

    source = [source, version_rc]

    vcxproj = env.MBGenVcxproj(target, source)

    binary = env.MBRunMSBuild(
        _get_windows_binary_target(env),
        vcxproj)

    env.Depends(binary, source)

    # Pick up any changes to this file that might not be seen by scons
    # This isn't normally necessary for a final product build system,
    # but when it's under development...
    env.Depends(vcxproj, env.File(CURRENT_FILE))
    env.Depends(binary, env.File(CURRENT_FILE))

    return binary

def mb_windows_program(env, target, source, *args, **kwargs):
    env[MB_WINDOWS_CONFIGURATION_TYPE] = APPLICATION_TYPE
    return _windows_binary(env, target, source)

def mb_windows_shared_library(env, target, source, *args, **kwargs):
    env[MB_WINDOWS_CONFIGURATION_TYPE] = DYNAMIC_LIB_TYPE
    return _windows_binary(env, target, source)

def mb_windows_static_library(env, target, source, *args, **kwargs):
    env[MB_WINDOWS_CONFIGURATION_TYPE] = STATIC_LIB_TYPE
    return _windows_binary(env, target, source)


# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--vcxproj-property',
        dest='vcxproj_properties',
        metavar='PROPERTY',
        type='string',
        action='append',
        default=[],
        help='WINDOWS_ONLY: Passes the given property=value pair to msbuild when building the project.')

    env.MBAddOption(
        '--hide-console',
        dest='hide_console',
        action='store_true',
        help='WINDOWS_ONLY: Normally we allow applications to display a console, so we can see printer errors, etc. This option turns that console off.')

    env.MBAddOption(
        '--bitness-override',
        dest='bitness_override',
        action='store',
        default=None,
        help='WINDOWS_ONLY: overrides the Platform setting. Use either Win32 or x64')

def mb_vcxproj_properties(env):
    properties = {}
    properties_list = env.MBGetOption('vcxproj_properties')
    for property_pair in properties_list:
        try:
            key, value = property_pair.split('=')
        except ValueError:
            raise Exception('Incorrectly specified property: need <property name>=<value>')
        properties[key] = value
    return properties

def bitness_override(env):
    return env.MBGetOption('bitness_override')

def mb_windows_bitness(env):
    if None == bitness_override(env):
        return env[MB_WINDOWS_PLATFORM_BITNESS]
    else:
        return bitness_override(env)

def mb_windows_is_64_bit(env):
    return 'x64' == env.MBWindowsBitness()

def mb_windows_is_32_bit(env):
    return 'Win32' == env.MBWindowsBitness()

def add_common_defines(env):
    env.Append(CPPDEFINES = ['_CRT_SECURE_NO_WARNINGS'])

def generate(env):
    env.Tool('common')
    env.Tool('log')
    env.Tool('rc')
    env.Tool('textfile')

    if env.MBIsWindows():
      common_arguments(env)

    # make sure that some necessary env variables exist
    env.SetDefault(**{
        MB_WINDOWS_STANDARD_CONFIG_DEFINES : [],
        MB_WINDOWS_PLATFORM_BITNESS : DEFAULT_PLATFORM_BITNESS,
        MB_WINDOWS_USE_SDL_CHECK : DEFAULT_USE_SDL_CHECK,
        MB_WINDOWS_IGNORED_LIBS : [],
        MB_WINDOWS_IS_WINDOWED_APPLICATION : False,
        MB_WINDOWS_API_IMPORTS: [],
        MB_WINDOWS_API_EXPORT: '',
        MB_WINDOWS_DISABLED_WARNINGS: []
    })

    env.AddMethod(mb_add_windows_devel_lib_path, 'MBAddWindowsDevelLibPath')
    env.AddMethod(mb_vcxproj_properties, 'MBVcxprojProperties')
    env.AddMethod(mb_windows_bitness, 'MBWindowsBitness')
    env.AddMethod(mb_windows_is_64_bit, 'MBWindowsIs64Bit')
    env.AddMethod(mb_windows_is_32_bit, 'MBWindowsIs32Bit')
    env.AddMethod(mb_set_windows_project_name, 'MBSetWindowsProjectName')
    env.AddMethod(mb_windows_add_standard_configuration_preprocessor_define,
        'MBWindowsAddStandardConfigurationPreprocessorDefine')
    env.AddMethod(mb_windows_add_api_import, 'MBWindowsAddAPIImport')
    env.AddMethod(mb_windows_set_api_export, 'MBWindowsSetAPIExport')
    env.AddMethod(mb_windows_set_default_api_export, 'MBWindowsSetDefaultAPIExport')
    env.AddMethod(mb_set_windows_use_sdl_check, 'MBSetWindowsUseSDLCheck')
    env.AddMethod(mb_add_windows_ignored_lib, 'MBAddWindowsIgnoredLib')
    env.AddMethod(mb_set_windows_is_windowed_application, 'MBSetWindowsIsWindowedApplication')
    env.AddMethod(mb_windows_disable_warning, 'MBWindowsDisableWarning')


    _gen_vcxproj_builder = SCons.Builder.Builder(
        action=SCons.Action.Action(
            _gen_vcxproj_action,
            "Creating vcxproj: '$TARGET'"),
        emitter=_gen_vcxproj_emitter,
        source_scanner=SCons.Tool.SourceFileScanner)

    env.Append(BUILDERS={'MBGenVcxproj': _gen_vcxproj_builder})
    env.AddMethod(_run_msbuild_method, 'MBRunMSBuild')

    env.AddMethod(mb_windows_program, 'MBWindowsProgram')
    env.AddMethod(mb_windows_shared_library, 'MBWindowsSharedLibrary')
    env.AddMethod(mb_windows_static_library, 'MBWindowsStaticLibrary')


    env.MBWindowsDisableWarning(
        '4251',
        '\n'.join([
            'C4251 warns that a function/class will not be usable by consumers of the generated DLL.',
            'This only matters if we try to use the function being warned about,',
            'in which case we would get errors anyway.']))

    if env.MBIsWindows():
      add_common_defines(env)

def exists(env):
    return True
