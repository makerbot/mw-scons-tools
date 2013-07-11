# Copyright 2013 MakerBot Industries

from SCons.Script import AddOption, GetOption
from optparse import OptionConflictError
import os, re
import xml.etree.ElementTree as ET

# environment keys
kDefaultConfiguration = 'MB_WINDOWS_DEFAULT_CONFIGURATION'

kCanBeProgram = 'MB_WINDOWS_CONFIGURATION_CAN_BE_PROGRAM'
kCanBeShared = 'MB_WINDOWS_CONFIGURATION_CAN_BE_SHARED'
kCanBeStatic = 'MB_WINDOWS_CONFIGURATION_CAN_BE_STATIC'

kPlatformBitness = 'MB_WINDOWS_PLATFROM_BITNESS'

kDependencies = 'MB_WINDOWS_PROJECT_DEPENDENCIES'

kProjectName = 'MB_WINDOWS_PROJECT_NAME'

def mb_add_windows_depencies(env, paths):
    ''' Adds dependecies on other .vcxprojs '''
    env.Append(MB_WINDOWS_PROJECT_DEPENDENCIES = paths)

def mb_set_windows_project_name(env, name):
    ''' Lots of things need a base name for the project '''
    env[kProjectName] = name
def mb_add_windows_dll_build_flag(env, flag):
    ''' So, this should really only be called once,
        but we're not going to enforce that '''
    env.Append(CPPDEFINES = flag)

def make_guid(project_name):
    ''' We want to make sure the guids are always the same per project name.
        Produces a guid in {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} form
        containing the project name (so don't reuse project names). '''
    fixed_name = project_name.replace('-', '')
    guid_base = fixed_name + '1234567890abcdef1234567890abcdef'
    project_guid = guid_base[0:8]+'-'+guid_base[8:12]+'-'+guid_base[12:16]+'-'+guid_base[16:20]+'-'+guid_base[20:32]
    return project_guid

def strip_obj(paths):
    ''' If any path starts with obj, remove the obj '''
    return [re.sub('^(\\\\|/)*obj(\\\\|/)*', '', path) for path in paths]

def one_per_line(prefix, stringlist, suffix):
    ''' Takes each element of a list and puts it on a separate
        line prefixed by 'prefix' and suffixed by 'suffix'.
        Returns it all as a string'''
    return '\n'.join([prefix + s + suffix for s in stringlist])

def fill_in_the_blanks(project_name,
                       can_be_program,
                       can_be_shared,
                       can_be_static,
                       default_configuration,
                       preprocessor_defines,
                       compiler_flags,
                       include_paths,
                       sources,
                       project_dependencies):
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
        '  <Import Project="$(MBRepoRoot)\site_scons\site_tools\mb_msvc_common.proj" />',
        '  <ItemDefinitionGroup>',
        '    <ClCompile>',
        '      <AdditionalOptions>',
        one_per_line('        ', compiler_flags, ''),
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
        '  </ItemDefinitionGroup>',
        '  <ItemGroup>',
        one_per_line('    <ClCompile Include="', strip_obj(sources), '" />'),
        '  </ItemGroup>',
        '  <ItemGroup>',
        one_per_line('    <ProjectReference Include="..\\', project_dependencies, '" />'),
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

    with open(filename, 'w') as f:
        f.write(fill_in_the_blanks(
            project_name = env[kProjectName],
            can_be_program = env[kCanBeProgram],
            can_be_shared = env[kCanBeShared],
            can_be_static = env[kCanBeStatic],
            default_configuration = configuration,
            compiler_flags = env['CCFLAGS'],
            preprocessor_defines = env['CPPDEFINES'],
            include_paths = [str(x) for x in env['CPPPATH']],
            sources = [str(x) for x in source],
            project_dependencies = env[kDependencies]))

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


    targets = [
        '#/obj/' + env[kPlatformBitness] + '/' + expandedname + '.' + target_type,
        '#/obj/' + env[kPlatformBitness] + '/' + expandedname + '.pdb'
    ]

    if target_type == kDynamicLibraryType:
        targets.append('#/obj/' + env[kPlatformBitness] + '/' + expandedname + '.lib')

    return targets, source

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
    command += ['/p:' + property for property in vcxproj_properties()]
    command += ['$SOURCE']

    msbuild = env.Command(target, source, ' '.join(command))

this_file = os.path.abspath(__file__)
def mb_windows_program(env, target, source, *args, **kwargs):
    ''' Generate a vcxproj and build it '''
    env.MBSetWindowsProjectName(target)
    vcxproj = env.MBGenVcxproj(target, source)
    env.Depends(vcxproj, this_file)
    program = env.MBBuildVcxproj(target, vcxproj)
    return program

# Set up command line args used by every scons script
def common_arguments():
    # This is pretty silly, but because we load this tool multiple times
    # these options can be loaded twice, which raises an error.
    # This error can be safely ignored.
    try:
        AddOption(
            '--vcxproj-property',
            dest='vcxproj_properties',
            metavar='PROPERTY',
            type='string',
            action='append',
            help='Passes the given property=value pair to msbuild when building the project.')

    except OptionConflictError:
        pass

def vcxproj_properties():
    return GetOption('vcxproj_properties')

def generate(env):
    common_arguments()

    # make sure that some necessary env variables exist
    if kDependencies not in env:
        env[kDependencies] = []

    if kPlatformBitness not in env:
        env[kPlatformBitness] = 'x64'

    if kCanBeProgram not in env:
        env[kCanBeProgram] = False

    if kCanBeShared not in env:
        env[kCanBeShared] = False

    if kCanBeStatic not in env:
        env[kCanBeStatic] = False

    env.AddMethod(mb_add_windows_depencies, 'MBAddWindowsDependency')

    env.AddMethod(mb_set_windows_project_name, 'MBSetWindowsProjectName')

    env.AddMethod(mb_add_windows_dll_build_flag, 'MBAddWindowsDLLBuildFlag')

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

def exists(env):
    return True
