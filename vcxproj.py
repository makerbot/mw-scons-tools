# Copyright 2013 MakerBot Industries

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

# Adds dependecies on sibling projects
def mb_add_windows_depencies(env, paths):
    env.Append(MB_WINDOWS_PROJECT_DEPENDENCIES = paths)

# Lots of things need a base name for the project
def mb_set_windows_project_name(env, name):
    env[kProjectName] = name

# So, this should really only be called once,
# but we're not going to enforce that
def mb_add_windows_dll_build_flag(env, flag):
    env.Append(CPPDEFINES = flag)

# we want to make sure the guids are always the same per project name
def make_guid(project_name):
    fixed_name = project_name.replace('-', '')
    guid_base = fixed_name + '1234567890abcdef1234567890abcdef'
    project_guid = guid_base[0:8]+'-'+guid_base[8:12]+'-'+guid_base[12:16]+'-'+guid_base[16:20]+'-'+guid_base[20:32]
    return project_guid

# if any path starts with obj, remove the obj
def strip_obj(paths):
  return [re.sub('^(\\\\|/)*obj(\\\\|/)*', '', path) for path in paths]

def one_per_line(prefix, stringlist, suffix):
    return '\n'.join([prefix + s + suffix for s in stringlist])

# this contains the template where the blanks can be filled in
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
        '  <Import Project="..\submodules\mw-scons-tools\mb_msvc_common.proj" />',
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

# Adds '.vcxproj' to the target
def mb_gen_vcxproj_emitter(target, source, env):
    target = [str(target[0]) + '.vcxproj']
    return target, source

# builds a .vcxproj with the given options
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

# Set default project configuration
def mb_windows_default_to_program(env):
    env[kDefaultConfiguration] = kProgramType
    env[kCanBeProgram] = True

def mb_windows_default_to_shared_lib(env):
    env[kDefaultConfiguration] = kDynamicLibraryType
    env[kCanBeShared] = True

def mb_windows_default_to_static_lib(env):
    env[kDefaultConfiguration] = kStaticLibraryType
    env[kCanBeStatic] = True

def mb_build_vcxproj_emitter(target, source, env):
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

# build the vcxproj, use it to build the project
def mb_build_vcxproj(env, target, source):
    # can't use an emitter with a Method, so manually call it
    target, source = mb_build_vcxproj_emitter(target, source, env)

    command = [
        'msbuild',
        '/p:MBConfiguration=' + ('Debug' if env.MBDebugBuild() else 'Release'),
        '/p:MBRepoRoot=' + str(env.Dir('#/.')) + '\\',
        '/p:Platform=' + env[kPlatformBitness],
        '$SOURCE'
    ]

    msbuild = env.Command(target, source, ' '.join(command))

def generate(env):
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

def exists(env):
    return True
