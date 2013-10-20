# Copyright 2013 MakerBot Industries

import os, re
import xml.etree.ElementTree as ET
import SCons

'''
Some conventions to keep this sane:
  * function definitions are in lowercase_with_underscores
  * if the function is exported by the tool, it starts with mb_
  * functions/builders are exported in camelcase, including the initial MB
  * functions are added in the same order as they appear in this file
Feel free to change the conventions if you think they're wrong,
just make sure to update everything to match those conventions
'''

# environment keys
DEFAULT_PLATFORM_BITNESS = 'x64'
MB_WINDOWS_PLATFORM_BITNESS = 'MB_WINDOWS_PLATFORM_BITNESS'

MB_WINDOWS_PROJECT_NAME = 'MB_WINDOWS_PROJECT_NAME'

DEFAULT_USE_SDL_CHECK = True
MB_WINDOWS_USE_SDL_CHECK = 'MB_WINDOWS_USE_SDL_CHECK'

MB_WINDOWS_IGNORED_LIBS = 'MB_WINDOWS_IGNORED_LIBS'

MB_WINDOWS_IS_WINDOWED_APPLICATION = 'MB_WINDOWS_IS_WINDOWED_APPLICATION'

MB_WINDOWS_API_IMPORTS = 'MB_WINDOWS_API_IMPORTS'
MB_WINDOWS_API_EXPORT = 'MB_WINDOWS_API_EXPORT'

MB_WINDOWS_STANDARD_CONFIG_DEFINES = 'MB_WINDOWS_STANDARD_CONFIG_DEFINES'

MB_WINDOWS_RESOURCES = 'MB_WINDOWS_RESOURCES'

DLL_IMPORT = '__declspec(dllimport)'
DLL_EXPORT = '__declspec(dllexport)'

# these function as both an enumeration and
# constant strings for each configuration type
APPLICATION_TYPE = {'extension': 'exe', 'project_string': 'Application'}
STATIC_LIB_TYPE =  {'extension': 'lib', 'project_string': 'StaticLibrary'}
DYNAMIC_LIB_TYPE = {'extension': 'dll', 'project_string': 'DynamicLibrary'}

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

def mb_windows_add_resource(env, rc):
    ''' Add a .rc file to the windows compilation '''
    env.Append(**{MB_WINDOWS_RESOURCES : [rc]})

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

def make_guid(project_name, debug, bitness):
    ''' We want to make sure the guids are always the same per project name.
        Produces a guid in {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} form
        based on the project name (so don't reuse project names). '''
    # convert project name to something readable as hex
    fixed_name = ''
    for char in project_name:
        fixed_name += str(ord(char))
    debug = ('D' if debug else '')
    bitness = ('64' if (bitness == 'x64') else '32')
    guid_base = bitness + debug + fixed_name + 'abcdef1234567890abcdef1234567890'
    project_guid = guid_base[0:8]+'-'+guid_base[8:12]+'-'+guid_base[12:16]+'-'+guid_base[16:20]+'-'+guid_base[20:32]
    return project_guid

def expand_project_name(project_name, target_type, debug):
    ''' Set up the target name with our naming convention '''
    expandedname = project_name

    if debug:
        expandedname += 'd'

    if target_type == STATIC_LIB_TYPE:
        expandedname = 'lib' + expandedname

    return expandedname

def configuration_string(debug):
    return 'Debug' if debug else 'Release'

def strip_obj(paths):
    ''' If any path starts with obj, remove the obj '''
    return [re.sub('^(\\\\|/)*obj(\\\\|/)*', '', path) for path in paths]

def replace_hash(paths):
    ''' Replace the '#' meaning 'root' with '' '''
    return [re.sub('^#(\\\\|/)*', '', path) for path in paths]

def replace_scons_nodes(nodes):
    ''' make all the Files and Nodes and Dirs and what-all into strings '''
    return [str(x) for x in nodes]

def desconsify(stuff):
    stuff = SCons.Util.flatten(stuff)
    stuff = replace_scons_nodes(stuff)
    stuff = replace_hash(stuff)
    return stuff

def one_per_line(prefix, stringlist, suffix):
    ''' Takes each element of a list and puts it on a separate
        line prefixed by 'prefix' and suffixed by 'suffix'.
        Returns it all as a string. '''
    return '\n'.join([prefix + s + suffix for s in stringlist])

def scons_to_msbuild_env_substitution(stuff):
    ''' Special handling of include_paths containing $ENVIRONMENT_VARIABLES
        because something replaces those correctly for other platforms
        but not on windows. $QT5DIR is the only one I've seen so far. '''
    return [re.sub('\\$([a-zA-Z0-9_]+)', '$(\\1)', thing) for thing in stuff]

def project_configurations(configuration, bitness):
    ''' Generate a 'ProjectConfiguration' node for the vcxproj '''
    return '\n'.join([
        '    <ProjectConfiguration Include="' + configuration + '|' + bitness + '">',
        '      <Configuration>' + configuration + '</Configuration>',
        '      <Platform>' + bitness + '</Platform>',
        '    </ProjectConfiguration>',
    ])

def configuration_group(configuration, configuration_type, debug, target_name, extra_properties):
    ''' Generate a 'PropertyGroup' node labeled 'Configuration' for the vcxproj.
        This is something that Visual Studio looks for. '''
    return '\n'.join([
        '  <PropertyGroup Condition="\'$(Configuration)\'==\'' + configuration + '\'" Label="Configuration">',
        '    <ConfigurationType>' + configuration_type + '</ConfigurationType>',
        '    <UseDebugLibraries>' + ('true' if debug else 'false') + '</UseDebugLibraries>',
        '    <PlatformToolset>v110</PlatformToolset>',
        '    <CharacterSet>Unicode</CharacterSet>',
        '    <TargetName>' + target_name + '</TargetName>',
        one_per_line('    ', extra_properties, ''),
        '  </PropertyGroup>',
    ])

def standard_project_configurations(debug, bitness):
    return project_configurations(configuration_string(debug), bitness)

def standard_configuration_group(project_name, debug, configuration_type, standard_config_defines):
    configuration = configuration_string(debug)

    extra_props = [
        '<!-- We use dynamic linkage against the C++ runtime by default -->',
        '<runtimeLinkType>DLL</runtimeLinkType>',
        '<importSiblings>' + DLL_IMPORT + '</importSiblings>',
        '<!-- There are some preprocessor defines that we only want in the standard config -->',
        '<PreprocessorDefinitions>',
        one_per_line('  ', standard_config_defines, ';'),
        '  $(PreprocessorDefinitions)',
        '</PreprocessorDefinitions>'
    ]

    target_name = expand_project_name(project_name, configuration_type, debug)

    return configuration_group(
        configuration,
        configuration_type['project_string'],
        debug,
        target_name,
        extra_props)

DRIVER_SUFFIX = '_lib_srt'

def driver_project_configurations(debug, bitness):
    ''' We have separate configurations for the driver so a .sln can easily call
        all the driver configurations. '''
    return project_configurations(configuration_string(debug) + DRIVER_SUFFIX, bitness)

def driver_configuration_group(project_name, debug):
    configuration = configuration_string(debug) + DRIVER_SUFFIX

    target_name = expand_project_name(project_name, STATIC_LIB_TYPE, debug)
    target_name += DRIVER_SUFFIX

    # we sometimes need things set in the driver but not otherwise
    extra_props = [
        '<driverConfiguration>true</driverConfiguration>',
    ]

    return configuration_group(
        configuration,
        STATIC_LIB_TYPE['project_string'],
        debug,
        target_name,
        extra_props)

def fill_in_the_blanks(debug,
                       bitness,
                       project_name,
                       api_imports,
                       api_export,
                       configuration_type,
                       standard_config_defines,
                       preprocessor_defines,
                       debugging_path,
                       use_sdl_check,
                       compiler_flags,
                       include_paths,
                       sources,
                       resources,
                       libs,
                       ignored_libs,
                       lib_paths,
                       hide_console):
    ''' this contains the template where the blanks can be filled in '''
    vcxproj_contents = '\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<Project DefaultTargets="Build" ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">',
        '  <ItemGroup Label="ProjectConfigurations">',
        standard_project_configurations(debug, bitness),
        driver_project_configurations(debug, bitness) if APPLICATION_TYPE != configuration_type else '',
        '  </ItemGroup>',
        '  <PropertyGroup Label="Globals">',
        '    <ProjectGuid>{' + make_guid(project_name, debug, bitness) + '}</ProjectGuid>',
        '    <RootNamespace>' + project_name + '</RootNamespace>',
        '  </PropertyGroup>',
        '  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />',
        standard_configuration_group(project_name, debug, configuration_type, standard_config_defines),
        driver_configuration_group(project_name, debug) if APPLICATION_TYPE != configuration_type else '',
        '  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />',
        '  <ImportGroup Label="ExtensionSettings">',
        '  </ImportGroup>',
        '  <ImportGroup Label="PropertySheets">',
        '    <Import Project="$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props" Condition="exists(\'$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props\')" Label="LocalAppDataPlatform" />',
        '  </ImportGroup>',
        '  <PropertyGroup Label="UserMacros" />',
        '  <PropertyGroup />',
        '  <PropertyGroup>',
        '    <!-- If running from scons, some properties may not be set up -->',
        '    <VCTargetsPath Condition="\'$(VCTargetsPath)\'==\'\'">C:\Program Files (x86)\MSBuild\Microsoft.Cpp\\v4.0\$(PlatformToolset)\</VCTargetsPath>',
        '    <!-- Paths -->',
        '    <!-- Standard Paths used by msbuild -->',
        '    <OutDir>$(ProjectDir)\obj\$(Platform)\</OutDir>',
        '    <IntDir>$(ProjectDir)\obj\$(RootNamespace)_Int\$(Platform)\$(Configuration)\</IntDir>',
        '    <!-- Some properties based on the Configuration -->',
        '    <MBIsDebug>' + ('true' if debug else 'false') + '</MBIsDebug>',
        '    <MBIsRelease>' + ('false' if debug else 'true') + '</MBIsRelease>',
        '    <MBPreprocessorDebugDefs Condition="$(MBIsDebug)">_DEBUG</MBPreprocessorDebugDefs>',
        '    <MBPreprocessorDebugDefs Condition="$(MBIsRelease)">NDEBUG</MBPreprocessorDebugDefs>',
        '    <apiDefine Condition="\'$(ConfigurationType)\' == \'DynamicLibrary\'">' + api_export + '=' + DLL_EXPORT + '</apiDefine>',
        '    <apiDefine Condition="\'$(ConfigurationType)\' != \'DynamicLibrary\'">' + api_export + '=</apiDefine>',
        '    <MBPreprocessorAPIDefs>',
        '      $(apiDefine);',
        one_per_line('      ', api_imports, '=$(importSiblings);'),
        '    </MBPreprocessorAPIDefs>',
        '    <!-- Adds a bunch of stuff to the path for debugging. Formatting matters a lot here. -->',
        '    <LocalDebuggerEnvironment>PATH=%PATH%;$(QT5DIR)\\bin;' + ';'.join(debugging_path),
        'QT_PLUGIN_PATH=$(QT5DIR)\plugins',
        '$(LocalDebuggerEnvironment)',
        '    </LocalDebuggerEnvironment>',
        '  </PropertyGroup>',
        '  <ItemDefinitionGroup>',
        '    <ClCompile>',
        '      <DebugInformationFormat>OldStyle</DebugInformationFormat>',
        '      <WarningLevel>Level3</WarningLevel>',
        '      <Optimization Condition="$(MBIsDebug)">Disabled</Optimization>',
        '      <Optimization Condition="$(MBIsRelease)">MaxSpeed</Optimization>',
        '      <FunctionLevelLinking>$(MBIsRelease)</FunctionLevelLinking>',
        '      <IntrinsicFunctions>$(MBIsRelease)</IntrinsicFunctions>',
        '      <SDLCheck>' + ('true' if use_sdl_check else 'false') + '</SDLCheck>',
        # AdditionalOptions can't be on individual lines because of a bug in msbuild
        '      <AdditionalOptions>' + ' '.join(compiler_flags),
        '        %(AdditionalOptions)',
        '      </AdditionalOptions>',
        '      <PreprocessorDefinitions>',
        '        $(MBPreprocessorDebugDefs);',
        '        $(MBPreprocessorAPIDefs);',
        one_per_line('        ', preprocessor_defines, ';'),
        '        $(PreprocessorDefinitions);',
        '        %(PreprocessorDefinitions)',
        '      </PreprocessorDefinitions>',
        '      <AdditionalIncludeDirectories>',
        one_per_line('        ', strip_obj(include_paths), ';'),
        '        %(AdditionalIncludeDirectories)',
        '      </AdditionalIncludeDirectories>',
        '      <BufferSecurityCheck>' + ('true' if debug else 'false') + '</BufferSecurityCheck>',
        '      <!-- We use dynamic linkage against the C++ runtime by default, but the driver uses static linkage -->',
        '      <RuntimeLibrary>MultiThreaded' + ('Debug' if debug else '') + '$(runtimeLinkType)</RuntimeLibrary>',
        '      <!-- Apparently the windows driver requires StdCall (but only on Win32, x64 has its own calling conventions -->',
        '      <CallingConvention Condition="$(driverConfiguration)">StdCall</CallingConvention>' if bitness == 'Win32' else '',
        '    </ClCompile>',
        '    <Link>',
        '      <GenerateDebugInformation>true</GenerateDebugInformation>',
        '      <EnableCOMDATFolding>$(MBIsRelease)</EnableCOMDATFolding>',
        '      <OptimizeReferences>$(MBIsRelease)</OptimizeReferences>',
        '      <AdditionalDependencies>',
        one_per_line('        ', libs, ';'),
        '        %(AdditionalDependencies)',
        '      </AdditionalDependencies>',
        '      <IgnoreSpecificDefaultLibraries>',
        one_per_line('        ', strip_obj(ignored_libs), ';'),
        '      </IgnoreSpecificDefaultLibraries>',
        '      <AdditionalLibraryDirectories>',
        one_per_line('        ', strip_obj(lib_paths), ';'),
        '        $(OutDir)',
        '        %(AdditionalLibraryDirectories)',
        '      </AdditionalLibraryDirectories>',
        '      <SubSystem>' + ('Windows' if hide_console else 'Console') + '</SubSystem>' if APPLICATION_TYPE == configuration_type else '',
        '    </Link>',
        '  </ItemDefinitionGroup>',
        '  <ItemGroup>',
        one_per_line('    <ClCompile Include="', strip_obj(sources), '" />'),
        '  </ItemGroup>',
        '  <ItemGroup>',
        one_per_line('    <ResourceCompile Include="', strip_obj(resources), '" />'),
        '  </ItemGroup>',
        '  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />',
        '</Project>'])

    return vcxproj_contents

def mb_gen_vcxproj_emitter(target, source, env):
    ''' An Emitter that adds '.vcxproj' to the target '''
    target = [str(target[0]) + '.vcxproj']
    return target, source

def gen_vcxproj(env, target, source, target_type):
    ''' Create an XML .vcxproj file
        Does most of the wrangling to get the data in an easily-printable
        format before passing it off to fill_in_the_blanks. '''

    filename = str(target[0])

    # clean up the CPPDEFINES, which can be strings, 1-tuples, 2-tuples, or dicts
    cppdefines = []
    for define in env['CPPDEFINES']:
        if isinstance(define, tuple):
            try:
                # 2-tuple
                cppdefines.append(define[0] + '=' + str(define[1]))
            except IndexError:
                # 1-tuple
                cppdefines.append(define[0])
        elif isinstance(define, dict):
            # dict
            for item in define.items():
                cppdefines.append(item[0] + '=' + str(item[1]))
        else:
            # string
            cppdefines.append(define)

    cpppath = desconsify(env['CPPPATH'])
    cpppath = scons_to_msbuild_env_substitution(cpppath)
    libpath = desconsify(env['LIBPATH'])
    libpath = scons_to_msbuild_env_substitution(libpath)

    libs = desconsify(env['LIBS'])
    # If there's a .dll, discard it. we can't link against dlls
    # and there's probably a .lib in there for it anyway.
    dllless_libs = []
    for lib in libs:
        if not lib.endswith('.dll'):
            dllless_libs.append(lib)
    libs = dllless_libs
    # manually append '.lib' if it's missing
    libs = [lib if lib.endswith('.lib') else lib + '.lib' for lib in libs]

    # we do less processing on ignored libs
    ignored_libs = SCons.Util.flatten(env[MB_WINDOWS_IGNORED_LIBS])

    with open(filename, 'w') as f:
        f.write(fill_in_the_blanks(
            debug = env.MBDebugBuild(),
            bitness = env.MBWindowsBitness(),
            project_name = env[MB_WINDOWS_PROJECT_NAME],
            api_imports = env[MB_WINDOWS_API_IMPORTS],
            api_export = env[MB_WINDOWS_API_EXPORT],
            configuration_type = target_type,
            standard_config_defines = env[MB_WINDOWS_STANDARD_CONFIG_DEFINES],
            debugging_path = libpath,
            compiler_flags = env['CCFLAGS'],
            preprocessor_defines = cppdefines,
            use_sdl_check = env[MB_WINDOWS_USE_SDL_CHECK],
            include_paths = cpppath,
            sources = desconsify(source),
            resources = desconsify(env[MB_WINDOWS_RESOURCES]),
            libs = libs,
            ignored_libs = ignored_libs,
            lib_paths = libpath,
            hide_console = hide_console(env)))

def mb_app_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, APPLICATION_TYPE)

def mb_dll_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, DYNAMIC_LIB_TYPE)

def mb_lib_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, STATIC_LIB_TYPE)

def mb_run_msbuild(env, target, source, configuration, platform, properties = []):
    command = [
        'msbuild',
        '/p:Configuration=' + configuration,
        '/p:Platform=' + platform]
    command += ['/p:' + property for property in properties]

    command += ['$SOURCE']

    target_list = env.Command(target, source, ' '.join(command))
    return target_list

def mb_build_vcxproj(env, target, source, target_type):
    ''' Build the given vcxproj '''
    expandedname = os.path.join(
        'obj',
        env.MBWindowsBitness(),
        expand_project_name(env[MB_WINDOWS_PROJECT_NAME],
                            target_type,
                            env.MBDebugBuild()))

    target = [expandedname + '.' + target_type['extension']]

    # For .dlls on windows we actually link against
    # the .lib that's generated, so return that, too
    if target_type == DYNAMIC_LIB_TYPE:
        target += [expandedname + '.lib']

    target_list = env.MBRunMSBuild(
        target,
        source,
        configuration_string(env.MBDebugBuild()),
        env.MBWindowsBitness(),
        vcxproj_properties(env))
    return target_list

this_file = os.path.abspath(__file__)
def windows_binary(env, target, source, configuration_type, *args, **kwargs):
    ''' Combines generating and building a vcxproj.
        Also sets up some dependencies.
        Also alters the names of the vcxproj files slightly. '''
    env.MBSetWindowsProjectName(target)
    vcxproj_name = target + ('_32' if env.MBWindowsIs32Bit() else '_64')
    vcxproj_name += ('d' if env.MBDebugBuild() else '')

    # TODO(ted): we can probably make this only regenerate if the version changes
    # TODO(ted): this path is kind of a hack, will probably cause trouble when something changes
    version_rc = env.MBGenerateVersionResource(
        vcxproj_name + '_version.rc',
        file_description = 'MakerBot Software',
        internal_name = target,
        original_filename = target,
        product_name = target)
    env.MBWindowsAddResource(version_rc)

    if APPLICATION_TYPE == configuration_type:
      vcxproj = env.MBAppVcxproj(vcxproj_name, source)
    elif DYNAMIC_LIB_TYPE == configuration_type:
      vcxproj = env.MBDLLVcxproj(vcxproj_name, source)
    elif STATIC_LIB_TYPE == configuration_type:
      vcxproj = env.MBLibVcxproj(vcxproj_name, source)

    env.Depends(vcxproj, version_rc)
    env.Depends(vcxproj, this_file)
    result = env.MBBuildVcxproj(target, vcxproj, configuration_type)
    env.Depends(result, source)
    return result

def mb_windows_program(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, APPLICATION_TYPE, *args, **kwargs)

def mb_windows_shared_library(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, DYNAMIC_LIB_TYPE, *args, **kwargs)

def mb_windows_static_library(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, STATIC_LIB_TYPE, *args, **kwargs)

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

def vcxproj_properties(env):
    return env.MBGetOption('vcxproj_properties')

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

def hide_console(env):
    return env.MBGetOption('hide_console') and env[MB_WINDOWS_IS_WINDOWED_APPLICATION]

def add_common_defines(env):
    env.Append(CPPDEFINES = ['_CRT_SECURE_NO_WARNINGS'])

def generate(env):
    env.Tool('common')
    env.Tool('log')
    env.Tool('rc')

    if env.MBIsWindows():
      common_arguments(env)

    # make sure that some necessary env variables exist
    env.SetDefault(**{
        MB_WINDOWS_RESOURCES : [],
        MB_WINDOWS_STANDARD_CONFIG_DEFINES : [],
        MB_WINDOWS_PLATFORM_BITNESS : DEFAULT_PLATFORM_BITNESS,
        MB_WINDOWS_USE_SDL_CHECK : DEFAULT_USE_SDL_CHECK,
        MB_WINDOWS_IGNORED_LIBS : [],
        MB_WINDOWS_IS_WINDOWED_APPLICATION : False,
        MB_WINDOWS_API_IMPORTS: [],
        MB_WINDOWS_API_EXPORT: ''
    })

    env.AddMethod(mb_add_windows_devel_lib_path, 'MBAddWindowsDevelLibPath')
    env.AddMethod(mb_windows_bitness, 'MBWindowsBitness')
    env.AddMethod(mb_windows_is_64_bit, 'MBWindowsIs64Bit')
    env.AddMethod(mb_windows_is_32_bit, 'MBWindowsIs32Bit')
    env.AddMethod(mb_set_windows_project_name, 'MBSetWindowsProjectName')
    env.AddMethod(mb_windows_add_standard_configuration_preprocessor_define,
        'MBWindowsAddStandardConfigurationPreprocessorDefine')
    env.AddMethod(mb_windows_add_resource, 'MBWindowsAddResource')
    env.AddMethod(mb_windows_add_api_import, 'MBWindowsAddAPIImport')
    env.AddMethod(mb_windows_set_api_export, 'MBWindowsSetAPIExport')
    env.AddMethod(mb_windows_set_default_api_export, 'MBWindowsSetDefaultAPIExport')
    env.AddMethod(mb_set_windows_use_sdl_check, 'MBSetWindowsUseSDLCheck')
    env.AddMethod(mb_add_windows_ignored_lib, 'MBAddWindowsIgnoredLib')
    env.AddMethod(mb_set_windows_is_windowed_application, 'MBSetWindowsIsWindowedApplication')

    import SCons.Tool
    env.Append(
        BUILDERS = {
            'MBAppVcxproj': env.Builder(
                action = mb_app_vcxproj,
                emitter = mb_gen_vcxproj_emitter,
                source_scanner = SCons.Tool.SourceFileScanner)})
    env.Append(
        BUILDERS = {
            'MBDLLVcxproj': env.Builder(
                action = mb_dll_vcxproj,
                emitter = mb_gen_vcxproj_emitter,
                source_scanner = SCons.Tool.SourceFileScanner)})
    env.Append(
        BUILDERS = {
            'MBLibVcxproj': env.Builder(
                action = mb_lib_vcxproj,
                emitter = mb_gen_vcxproj_emitter,
                source_scanner = SCons.Tool.SourceFileScanner)})

    env.AddMethod(mb_run_msbuild, 'MBRunMSBuild')
    env.AddMethod(mb_build_vcxproj, 'MBBuildVcxproj')

    env.AddMethod(mb_windows_program, 'MBWindowsProgram')
    env.AddMethod(mb_windows_shared_library, 'MBWindowsSharedLibrary')
    env.AddMethod(mb_windows_static_library, 'MBWindowsStaticLibrary')

    if env.MBIsWindows():
      add_common_defines(env)

def exists(env):
    return True
