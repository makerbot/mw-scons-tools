import SCons
import collections
import os
import re
import subprocess

def warning(message, path, line_number = None):
    """Print a gcc-style warning"""
    print(
        '{}:{}: warning: {}'.format(
            path,
            str(line_number) if line_number else 0,
            message))

class DoxygenConfig:
    """In-memory Doxygen configuration"""

    class _Value:
        """Line number and value for a configuration key"""
        def __init__(self, value, line_number = None):
            self.value = value
            self.line_number = line_number

    def __init__(self, config_path):
        self.original_path = str(config_path.srcnode())
        with open(str(config_path), 'r') as config_file:
            self._config = self._parse(config_file)

    def _parse(self, config_file):
        """Parse Doxygen configuration file into an OrderedDict"""
        kv = collections.OrderedDict()
        line_number = 0
        for line in config_file.readlines():
            line_number += 1
            # Strip comment
            line = line[:line.find('#')]
            # Look for key = value
            match = re.search(r'(\w+)\s*=\s*(.*)', line)
            if match:
                key, value = match.group(1, 2)
                kv[key] = self._Value(value.strip(), line_number)
        return kv

    def override_config_value(self, key, value):
        """Set a configuration value, warn if already set"""
        if key in self._config:
            if self._config[key].value != '':
                warning(
                    'overriding configuration {}'.format(key),
                    self.original_path,
                    self._config[key].line_number)
                self._config[key].value = value
            else:
                self._config[key] = self._Value(value)

    def ensure_config_value(self, key, expected_value):
        """Ensure that a configuration value is correct

        If the key already has the expected_value, do nothing.
        Otherwise, print a warning and set the correct value.
        """
        if key in self._config:
            if self._config[key].value != expected_value:
                warning(
                    'overriding configuration {} with {}'.format(
                        key, expected_value),
                    self.original_path,
                    self._config[key].line_number)
        else:
            warning(
                'warning: adding missing configuration {} = {}'.format(
                    key, expected_value),
                self.original_path)
            self._config[key] = expected_value
            
    def write_config(self, path):
        """Write Doxygen configuration dict to a file"""
        with open(path, 'w') as f:
            for k in self._config:
                f.write('{} = {}\n'.format(k, self._config[k].value))

class DoxygenBinary:
    @staticmethod
    def is_runnable():
        """Return true if Doxygen runs, false otherwise"""
        try:
            subprocess.check_output('doxygen', stderr=subprocess.STDOUT)
            return True
        except OSError:
            return False

    @staticmethod
    def invoke(config_path):
        """Run Doxygen on specificed configuration file"""
        subprocess.call(['doxygen', config_path])

def generate(env):
    expected_output = os.path.join('html', 'index.html')

    def DoxygenBuilderAction(env, target, source):
        if DoxygenBinary.is_runnable():
            # Strip off the expected portion of the output path
            target = target[0].get_abspath()
            if target.endswith(expected_output):
                target = target[:-len(expected_output)]
            else:
                raise Exception('Only HTML output is currently supported')

            # Split source list into configuration file and everything else
            config_path = source[0]
            source = source[1:]

            # Modify configuration
            config = DoxygenConfig(config_path)
            config.override_config_value('INPUT', ' '.join(str(s) for s in source))
            config.override_config_value('OUTPUT_DIRECTORY', target)
            config.ensure_config_value('GENERATE_HTML', 'YES')
            config.ensure_config_value('HTML_OUTPUT', 'html')

            # Write generated Doxygen configuration file
            config_subst_path = str(config_path) + '.subst'
            config.write_config(config_subst_path)

            # Generate Doxygen output
            DoxygenBinary.invoke(config_subst_path)
        else:
            print('Doxygen not found')

    env.Append(
        BUILDERS = {
            'DoxygenBuilder':
                env.Builder(action = DoxygenBuilderAction)})

    def BuildDoxygen(env, configuration, *sources):
        """Run Doxygen using configuration on specified sources"""
        all_source = (configuration,) + sources
        env.DoxygenBuilder(
            'doxygen/' + expected_output,
            all_source)
        # Ensure that documentation is always built, even if only the
        # "install" target is specified
        SCons.Script.BUILD_TARGETS.append(env.File('doxygen/html/index.html'))

    env.AddMethod(BuildDoxygen, 'BuildDoxygen')

def exists(env):
    return True
