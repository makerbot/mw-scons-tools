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
kDefaultPlatformBitness = 'x64'
kPlatformBitness = 'MB_WINDOWS_PLATFORM_BITNESS'

kProjectName = 'MB_WINDOWS_PROJECT_NAME'

kDefaultUseSDLCheck = True
kUseSDLCheck = 'MB_WINDOWS_USE_SDL_CHECK'

# for the --novariant option
kVariantDir = 'MB_WINDOWS_VARIANT_DIR'

kIgnoredLibs = 'MB_WINDOWS_IGNORED_LIBS'


def mb_add_windows_devel_lib_path(env, path, platform = None):
    ''' Adds dependecies on other projects' output '''
    if None == platform:
        platform = env[kPlatformBitness]
    env.Prepend(LIBPATH = [str(env.Dir(os.path.join(path, platform)))])

def mb_set_windows_bitness(env, bitness):
    ''' Toggle between Win32 and x64 '''
    env[kPlatformBitness] = bitness

def mb_windows_is_64_bit(env):
    return 'x64' == env[kPlatformBitness]

def mb_windows_is_32_bit(env):
    return 'Win32' == env[kPlatformBitness]

def mb_set_windows_project_name(env, name):
    ''' Lots of things need a base name for the project '''
    env[kProjectName] = name

def mb_add_windows_dll_build_flag(env, flag):
    ''' So, this should really only be called once,
        but we're not going to enforce that '''
    env.Append(CPPDEFINES = flag)

def mb_set_windows_use_sdl_check(env, use_sdl):
    env[kUseSDLCheck] = use_sdl

def mb_set_windows_variant_dir(env, variant_dir):
    env[kVariantDir] = variant_dir

def mb_add_windows_ignored_lib(env, lib):
    env.Append(**{kIgnoredLibs : [lib]})

def make_guid(project_name):
    ''' We want to make sure the guids are always the same per project name.
        Produces a guid in {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} form
        based on the project name (so don't reuse project names). '''
    # convert project name to something readable as hex
    fixed_name = ''
    for char in project_name:
        fixed_name += str(ord(char))
    guid_base = fixed_name + 'abcdef1234567890abcdef1234567890'
    project_guid = guid_base[0:8]+'-'+guid_base[8:12]+'-'+guid_base[12:16]+'-'+guid_base[16:20]+'-'+guid_base[20:32]
    return project_guid

def strip_obj(paths):
    ''' If any path starts with obj, remove the obj '''
    return [re.sub('^(\\\\|/)*obj(\\\\|/)*', '', path) for path in paths]

def replace_hash(paths):
    ''' Replace the '#' meaning 'root' with '..' '''
    return [re.sub('^#', '..', path) for path in paths]

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

def project_configurations(debug, bitness, suffix):
    configuration = 'Debug' if debug else 'Release'
    configuration += suffix
    return '\n'.join([
        '    <ProjectConfiguration Include="' + configuration + '|' + bitness + '">',
        '      <Configuration>' + configuration + '</Configuration>',
        '      <Platform>' + bitness + '</Platform>',
        '    </ProjectConfiguration>',
    ])

def configuration_group(debug, configuration_type, suffix):
    configuration = 'Debug' if debug else 'Release'
    configuration += suffix

    configuration_type = ('Application' if kProgramType == configuration_type else
        ('DynamicLibrary' if kDynamicLibraryType == configuration_type else
        'StaticLibrary'))

    return '\n'.join([
        '  <PropertyGroup Condition="\'$(Configuration)\'==\'' + configuration + '\'" Label="Configuration">',
        '    <ConfigurationType>' + configuration_type + '</ConfigurationType>',
        '    <UseDebugLibraries>' + ('true' if debug else 'false') + '</UseDebugLibraries>',
        '    <PlatformToolset>v110</PlatformToolset>',
        '    <CharacterSet>MultiByte</CharacterSet>',
        '    <configSuffix>' + suffix + '</configSuffix>',
        '  </PropertyGroup>',
    ])

def fill_in_the_blanks(debug,
                       bitness,
                       project_name,
                       target_name,
                       lib_name,
                       configuration_type,
                       preprocessor_defines,
                       debugging_path,
                       use_sdl_check,
                       compiler_flags,
                       include_paths,
                       sources,
                       libs,
                       ignored_libs,
                       lib_paths):
    ''' this contains the template where the blanks can be filled in '''
    vcxproj_contents = '\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<Project DefaultTargets="Build" ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">',
        '  <ItemGroup Label="ProjectConfigurations">',
        project_configurations(debug, bitness, ''),
        project_configurations(debug, bitness, '_lib') if kDynamicLibraryType == configuration_type else '',
        '  </ItemGroup>',
        '  <PropertyGroup Label="Globals">',
        '    <ProjectGuid>{' + make_guid(project_name) + '}</ProjectGuid>',
        '    <RootNamespace>' + project_name + '</RootNamespace>',
        '  </PropertyGroup>',
        '  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />',
        configuration_group(debug, configuration_type, ''),
        configuration_group(debug, kStaticLibraryType, '_lib') if kDynamicLibraryType == configuration_type else '',
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
        '    <MBRepoRoot>$(ProjectDir)\..\</MBRepoRoot>',
        '    <MBToolchainFolder>$(MBRepoRoot)\..\</MBToolchainFolder>',
        '    <variantDir Condition="\'$(MBNoVariant)\' == \'\' Or \'$(MBNoVariant)\' == \'false\'">.\obj\</variantDir>',
        '    <variantDir Condition="\'$(MBNoVariant)\' != \'\'">.\</variantDir>',
        '    <outputSuffix>$(variantDir)\$(Platform)\</outputSuffix>',
        '    <!-- Standard Paths used by msbuild -->',
        '    <OutDir>$(MBRepoRoot)$(outputSuffix)</OutDir>',
        '    <IntDir>$(ProjectDir)$(ProjectName)_Int\$(Platform)\$(Configuration)\</IntDir>',
        '    <!-- Some properties based on the Configuration -->',
        '    <MBIsDebug>' + ('true' if debug else 'false') + '</MBIsDebug>',
        '    <MBIsRelease>' + ('false' if debug else 'true') + '</MBIsRelease>',
        '    <MBPreprocessorDebugDefs Condition="\'$(MBIsDebug)\' == \'true\'">_DEBUG</MBPreprocessorDebugDefs>',
        '    <MBPreprocessorDebugDefs Condition="\'$(MBIsRelease)\' == \'true\'">NDEBUG</MBPreprocessorDebugDefs>',
        '    <TargetName Condition="\'$(configSuffix)\' == \'\'">' + target_name + '</TargetName>',
        '    <TargetName Condition="\'$(configSuffix)\' == \'_lib\'">' + lib_name + '</TargetName>' if kDynamicLibraryType == configuration_type else '',
        '    <!-- Adds a bunch of stuff to the path for debugging. Formatting matters a lot here. -->',
        '    <LocalDebuggerEnvironment>PATH=%PATH%;$(QT5DIR)\\bin;' + ';'.join(debugging_path),
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
        one_per_line('        ', preprocessor_defines, ';'),
        '        %(PreprocessorDefinitions)',
        '      </PreprocessorDefinitions>',
        '      <AdditionalIncludeDirectories>',
        one_per_line('        ', strip_obj(include_paths), ';'),
        '        %(AdditionalIncludeDirectories)',
        '      </AdditionalIncludeDirectories>',
        '    </ClCompile>',
        '    <Link>',
        '      <GenerateDebugInformation>true</GenerateDebugInformation>',
        '      <EnableCOMDATFolding>$(MBIsRelease)</EnableCOMDATFolding>',
        '      <OptimizeReferences>$(MBIsRelease)</OptimizeReferences>',
        '      <AdditionalDependencies>',
        one_per_line('        ', strip_obj(libs), ';'),
        '        %(AdditionalDependencies)',
        '      </AdditionalDependencies>',
        '      <IgnoreSpecificDefaultLibraries>',
        one_per_line('        ', strip_obj(ignored_libs), ';'),
        '      </IgnoreSpecificDefaultLibraries>',
        '      <AdditionalLibraryDirectories>',
        one_per_line('        ', strip_obj(lib_paths), ';'),
        '        %(AdditionalLibraryDirectories)',
        '      </AdditionalLibraryDirectories>',
        '    </Link>',
        '  </ItemDefinitionGroup>',
        '  <ItemGroup>',
        one_per_line('    <ClCompile Include="', strip_obj(sources), '" />'),
        '  </ItemGroup>',
        '  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />',
        '</Project>'])

    return vcxproj_contents

# these function as both an enumeration and
# the file extensions for each configuration type
kProgramType = 'exe'
kStaticLibraryType = 'lib'
kDynamicLibraryType = 'dll'

def expanded_project_name(env, target_type):
    ''' Set up the target name with our naming convention '''
    expandedname = env[kProjectName]

    if env.MBDebugBuild():
        expandedname += 'd'

    if target_type == kStaticLibraryType:
        expandedname = 'lib' + expandedname

    return expandedname

def mb_gen_vcxproj_emitter(target, source, env):
    ''' An Emitter that adds '.vcxproj' to the target '''
    target = [str(target[0]) + '.vcxproj']
    return target, source

def gen_vcxproj(env, target, source, target_type):
    '''Create an XML .vcxproj file'''

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
    ignored_libs = SCons.Util.flatten(env[kIgnoredLibs])

    with open(filename, 'w') as f:
        f.write(fill_in_the_blanks(
            debug = env.MBDebugBuild(),
            bitness = env[kPlatformBitness],
            project_name = env[kProjectName],
            target_name = expanded_project_name(env, target_type),
            lib_name = expanded_project_name(env, kStaticLibraryType),
            configuration_type = target_type,
            debugging_path = libpath,
            compiler_flags = env['CCFLAGS'],
            preprocessor_defines = cppdefines,
            use_sdl_check = env[kUseSDLCheck],
            include_paths = cpppath,
            sources = desconsify(source),
            libs = libs,
            ignored_libs = ignored_libs,
            lib_paths = libpath))

def mb_app_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, kProgramType)

def mb_dll_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, kDynamicLibraryType)

def mb_lib_vcxproj(target, source, env):
    gen_vcxproj(env, target, source, kStaticLibraryType)

def mb_build_vcxproj(env, target, source, target_type):
    ''' Build the given vcxproj (we assume that it's a vcxproj generated by us,
        (and therefore understands things like MBConfiguration '''
    expandedname = expanded_project_name(env, target_type)

    target = [os.path.join(
        '#',
        'obj',
        env[kPlatformBitness],
        (expandedname + '.' + target_type))]

    # For .dlls on windows we actually link against
    # the .lib that's generated, so return that, too
    if target_type == kDynamicLibraryType:
        target.append(
            os.path.join(
                '#',
                'obj',
                env[kPlatformBitness],
                (expandedname + '.lib')))

    # this supposedly fixes problems with paths containing spaces
    formatted_repo_root = str(env.Dir('#/.'))
    formatted_repo_root = re.sub('\\\\', '\\\\\\\\', formatted_repo_root)

    command = [
        'msbuild',
        '/p:Configuration=' + ('Debug' if env.MBDebugBuild() else 'Release'),
        '/p:MBRepoRoot="' + formatted_repo_root + '\\\\"',
        '/p:Platform=' + env[kPlatformBitness]]
    command += ['/p:' + property for property in vcxproj_properties(env)]
    # only in miracle-grue at the moment
    try:
        if env.GetOption('novariant'):
            command += ['/p:MBNoVariant=true']
    except AttributeError:
        pass
    command += ['$SOURCE']

    target_list = env.Command(target, source, ' '.join(command))
    return target_list

def windows_binary(env, target, source, configuration_type, *args, **kwargs):
    env.MBSetWindowsProjectName(target)
    if kProgramType == configuration_type:
      vcxproj = env.MBAppVcxproj(target, source)
    elif kDynamicLibraryType == configuration_type:
      vcxproj = env.MBDLLVcxproj(target, source)
    elif kStaticLibraryType == configuration_type:
      vcxproj = env.MBLibVcxproj(target, source)
    this_file = os.path.abspath(__file__)
    env.Depends(vcxproj, this_file)
    result = env.MBBuildVcxproj(target, vcxproj, configuration_type)
    env.Depends(result, source)
    return result

def mb_windows_program(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, kProgramType, *args, **kwargs)

def mb_windows_shared_library(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, kDynamicLibraryType, *args, **kwargs)

def mb_windows_static_library(env, target, source, *args, **kwargs):
    return windows_binary(env, target, source, kStaticLibraryType, *args, **kwargs)

# Set up command line args used by every scons script
def common_arguments(env):
    env.MBAddOption(
        '--vcxproj-property',
        dest='vcxproj_properties',
        metavar='PROPERTY',
        type='string',
        action='append',
        default=[],
        help='Passes the given property=value pair to msbuild when building the project.')

def vcxproj_properties(env):
    return env.MBGetOption('vcxproj_properties')

def add_common_defines(env):
    env.Append(CPPDEFINES = ['_CRT_SECURE_NO_WARNINGS'])

def generate(env):
    env.Tool('options')
    env.Tool('log')

    common_arguments(env)

    # make sure that some necessary env variables exist
    env.SetDefault(**{
        kPlatformBitness : kDefaultPlatformBitness,
        kUseSDLCheck : kDefaultUseSDLCheck,
        kIgnoredLibs : []
    })

    env.AddMethod(mb_add_windows_devel_lib_path, 'MBAddWindowsDevelLibPath')
    env.AddMethod(mb_set_windows_bitness, 'MBSetWindowsBitness')
    env.AddMethod(mb_windows_is_64_bit, 'MBWindowsIs64Bit')
    env.AddMethod(mb_windows_is_32_bit, 'MBWindowsIs32Bit')
    env.AddMethod(mb_set_windows_project_name, 'MBSetWindowsProjectName')
    env.AddMethod(mb_add_windows_dll_build_flag, 'MBAddWindowsDLLBuildFlag')
    env.AddMethod(mb_set_windows_use_sdl_check, 'MBSetWindowsUseSDLCheck')
    env.AddMethod(mb_add_windows_ignored_lib, 'MBAddWindowsIgnoredLib')

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

    env.AddMethod(mb_build_vcxproj, 'MBBuildVcxproj')

    env.AddMethod(mb_windows_program, 'MBWindowsProgram')
    env.AddMethod(mb_windows_shared_library, 'MBWindowsSharedLibrary')
    env.AddMethod(mb_windows_static_library, 'MBWindowsStaticLibrary')

    add_common_defines(env)

def exists(env):
    return True
