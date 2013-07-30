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
kDefaultConfiguration = 'MB_WINDOWS_DEFAULT_CONFIGURATION'

kCanBeProgram = 'MB_WINDOWS_CONFIGURATION_CAN_BE_PROGRAM'
kCanBeShared = 'MB_WINDOWS_CONFIGURATION_CAN_BE_SHARED'
kCanBeStatic = 'MB_WINDOWS_CONFIGURATION_CAN_BE_STATIC'

kDefaultPlatformBitness = 'x64'
kPlatformBitness = 'MB_WINDOWS_PLATFORM_BITNESS'

kProjectName = 'MB_WINDOWS_PROJECT_NAME'

kDefaultUseSDLCheck = True
kUseSDLCheck = 'MB_WINDOWS_USE_SDL_CHECK'

# for the --novariant option
kVariantDir = 'MB_WINDOWS_VARIANT_DIR'

def mb_add_windows_devel_lib_path(env, path, platform = None):
    ''' Adds dependecies on other projects' output '''
    if None == platform:
        platform = env[kPlatformBitness]
    env.Prepend(LIBPATH = [str(env.Dir(os.path.join(path, platform)))])

def mb_set_windows_bitness(env, bitness):
    ''' Toggle between Win32 and x64 '''
    env[kPlatformBitness] = bitness

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

def make_guid(project_name):
    ''' We want to make sure the guids are always the same per project name.
        Produces a guid in {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} form
        based on the project name (so don't reuse project names). '''
    fixed_name = project_name.replace('-', '')
    fixed_name = project_name.replace('_', '')
    guid_base = fixed_name + '1234567890abcdef1234567890abcdef'
    project_guid = guid_base[0:8]+'-'+guid_base[8:12]+'-'+guid_base[12:16]+'-'+guid_base[16:20]+'-'+guid_base[20:32]
    return project_guid

def strip_obj(paths):
    ''' If any path starts with obj, remove the obj '''
    return [re.sub('^(\\\\|/)*obj(\\\\|/)*', '', path) for path in paths]

def replace_hash(paths):
    ''' If any path starts with obj, remove the obj '''
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

def fill_in_the_blanks(project_name,
                       can_be_program,
                       can_be_shared,
                       can_be_static,
                       default_configuration,
                       preprocessor_defines,
                       use_sdl_check,
                       compiler_flags,
                       include_paths,
                       sources,
                       libs,
                       lib_paths):
    ''' this contains the template where the blanks can be filled in '''
    vcxproj_contents = '\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<Project DefaultTargets="Build" ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">',
        '  <PropertyGroup Label="Globals">',
        '    <ProjectGuid>{' + make_guid(project_name) + '}</ProjectGuid>',
        '    <RootNamespace>' + project_name + '</RootNamespace>',
        '  </PropertyGroup>',
        '  <PropertyGroup>',
        '    <MBCanBeLib>' + ('true' if can_be_static else 'false') + '</MBCanBeLib>',
        '    <MBCanBeDLL>' + ('true' if can_be_shared else 'false') + '</MBCanBeDLL>',
        '    <MBCanBeApp>' + ('true' if can_be_program else 'false') + '</MBCanBeApp>',
        '    <MBDefaultConfigurationType>' + default_configuration + '</MBDefaultConfigurationType>',
        '  </PropertyGroup>',
        '  <Import Project=".\site_scons\site_tools\mb_msvc_common.proj" />',
        '  <ItemDefinitionGroup>',
        '    <ClCompile>',
        '      <SDLCheck>' + ('true' if use_sdl_check else 'false') + '</SDLCheck>',
        '      <AdditionalOptions>' + ' '.join(compiler_flags),
        '        %(AdditionalOptions)',
        '      </AdditionalOptions>',
        '      <PreprocessorDefinitions>',
        '        $(MBCommonPreprocessorDefs);',
        one_per_line('        ', preprocessor_defines, ';'),
        '        %(PreprocessorDefinitions)',
        '      </PreprocessorDefinitions>',
        '      <AdditionalIncludeDirectories>',
        one_per_line('        ', strip_obj(include_paths), ';'),
        '        %(AdditionalIncludeDirectories)',
        '      </AdditionalIncludeDirectories>',
        '    </ClCompile>',
        '    <Link>',
        '      <AdditionalDependencies>',
        one_per_line('        ', strip_obj(libs), ';'),
        '        %(AdditionalDependencies)',
        '      </AdditionalDependencies>',
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

def mb_gen_vcxproj_emitter(target, source, env):
    ''' An Emitter that adds '.vcxproj' to the target '''
    target = [str(target[0]) + '.vcxproj']
    return target, source

def mb_gen_vcxproj(target, source, env):
    '''Create an XML .vcxproj file'''

    filename = str(target[0])

    default_to_program = (kProgramType == env[kDefaultConfiguration])
    default_to_shared = (kDynamicLibraryType == env[kDefaultConfiguration])
    default_to_static = (kStaticLibraryType == env[kDefaultConfiguration])

    configuration = ('Application' if default_to_program else
        ('DynamicLibrary' if default_to_shared else 'StaticLibrary'))

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

    env.MBLogSpam(
        'project_name = ' + str(env[kProjectName]) + '\n' +
        'can_be_program = ' + str(env[kCanBeProgram]) + '\n' +
        'can_be_shared = ' + str(env[kCanBeShared]) + '\n' +
        'can_be_static = ' + str(env[kCanBeStatic]) + '\n' +
        'default_configuration = ' + str(configuration) + '\n' +
        'compiler_flags = ' + str(env['CCFLAGS']) + '\n' +
        'preprocessor_defines = ' + str(cppdefines) + '\n' +
        'use_sdl_check = ' + str(env[kUseSDLCheck]) + '\n' +
        'include_paths = ' + str(cpppath) + '\n' +
        'sources = ' + str(desconsify(source)) + '\n' +
        'libs = ' + str(libs) + '\n' +
        'lib_paths = ' + str(libpath))

    with open(filename, 'w') as f:
        f.write(fill_in_the_blanks(
            project_name = env[kProjectName],
            can_be_program = env[kCanBeProgram],
            can_be_shared = env[kCanBeShared],
            can_be_static = env[kCanBeStatic],
            default_configuration = configuration,
            compiler_flags = env['CCFLAGS'],
            preprocessor_defines = cppdefines,
            use_sdl_check = env[kUseSDLCheck],
            include_paths = cpppath,
            sources = desconsify(source),
            libs = libs,
            lib_paths = libpath))

def mb_windows_default_to_program(env):
    ''' Set default project configuration to Application/exe '''
    env[kDefaultConfiguration] = kProgramType
    env[kCanBeProgram] = True

def mb_windows_default_to_shared_lib(env):
    ''' Set default project configuration to DynamicLibrary/dll+lib '''
    env[kDefaultConfiguration] = kDynamicLibraryType
    env[kCanBeShared] = True

def mb_windows_default_to_static_lib(env):
    ''' Set default project configuration to StaticLibrary/lib '''
    env[kDefaultConfiguration] = kStaticLibraryType
    env[kCanBeStatic] = True

def mb_build_vcxproj_emitter(target, source, env):
    ''' Emitter to turn a project name into the outputs
        of the vcxproj in the default configuration '''
    target_type = env[kDefaultConfiguration]

    expandedname = env[kProjectName]
    if env.MBDebugBuild():
        expandedname += 'd'

    if target_type == kStaticLibraryType:
        expandedname = 'lib' + expandedname

    extension = target_type

    target = [os.path.join(
        '#',
        'obj',
        env[kPlatformBitness],
        (expandedname + '.' + extension))]

    # For .dlls on windows we actually link against
    # the .lib that's generated, so return that, too
    if target_type == kDynamicLibraryType:
        target.append(
            os.path.join(
                '#',
                'obj',
                env[kPlatformBitness],
                (expandedname + '.lib')))

    return target, source

def mb_build_vcxproj(env, target, source):
    ''' Build the given vcxproj (we assume that it's a vcxproj generated by us,
        (and therefore understands things like MBConfiguration '''
    # can't use an emitter with a Method, so manually call it
    target, source = mb_build_vcxproj_emitter(target, source, env)

    command = [
        'msbuild',
        '/p:MBConfiguration=' + ('Debug' if env.MBDebugBuild() else 'Release'),
        '/p:MBRepoRoot=' + str(env.Dir('#/.')) + '\\',
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

def mb_windows_program(env, target, source, *args, **kwargs):
    ''' Generate a vcxproj and build it '''
    env.MBSetWindowsProjectName(target)
    vcxproj = env.MBGenVcxproj(target, source)
    this_file = os.path.abspath(__file__)
    env.Depends(vcxproj, this_file)
    common_file = env.File('site_scons\site_tools\mb_msvc_common.proj')
    env.Depends(vcxproj, common_file)
    return env.MBBuildVcxproj(target, vcxproj)

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
    if kPlatformBitness not in env:
        env[kPlatformBitness] = kDefaultPlatformBitness

    if kUseSDLCheck not in env:
        env[kUseSDLCheck] = kDefaultUseSDLCheck

    if kCanBeProgram not in env:
        env[kCanBeProgram] = False

    if kCanBeShared not in env:
        env[kCanBeShared] = False

    if kCanBeStatic not in env:
        env[kCanBeStatic] = False

    env.AddMethod(mb_add_windows_devel_lib_path, 'MBAddWindowsDevelLibPath')
    env.AddMethod(mb_set_windows_bitness, 'MBSetWindowsBitness')
    env.AddMethod(mb_set_windows_project_name, 'MBSetWindowsProjectName')
    env.AddMethod(mb_add_windows_dll_build_flag, 'MBAddWindowsDLLBuildFlag')
    env.AddMethod(mb_set_windows_use_sdl_check, 'MBSetWindowsUseSDLCheck')

    env.AddMethod(mb_windows_default_to_program, 'MBWindowsDefaultToProgram')
    env.AddMethod(mb_windows_default_to_static_lib, 'MBWindowsDefaultToStaticLib')
    env.AddMethod(mb_windows_default_to_shared_lib, 'MBWindowsDefaultToSharedLib')

    import SCons.Tool
    env.Append(
        BUILDERS = {
            'MBGenVcxproj': env.Builder(
                action = mb_gen_vcxproj,
                emitter = mb_gen_vcxproj_emitter,
                source_scanner = SCons.Tool.SourceFileScanner)})

    env.AddMethod(mb_build_vcxproj, 'MBBuildVcxproj')

    env.AddMethod(mb_windows_program, 'MBWindowsProgram')

    add_common_defines(env)

def exists(env):
    return True
