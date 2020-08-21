#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
.. moduleauthor:: John Brännström <john.brannstrom@gmail.com>

Bash install
************

This is a program installer module. It can be used to install a program on a
Linux system and prepare the Linux environment for a program to run properly.
This script requires bash.

"""

# Built in modules
import subprocess
import argparse
import os
import sys
import re


class YesNoError(Exception):
    """Error for malformed yes/no value."""

    def __init__(self, yes_no: str):
        """
        Constructor function.
        :param yes_no: Yes/no value that caused the error.
        """
        message = 'Error, "{yes_no}" is not a valid yes/no value!'
        self._message = message.format(yes_no=yes_no)

    # noinspection PyUnresolvedReferences
    def __str__(self):
        """
        String representation function.
        """
        return self._message


class BashInstall:
    """Installer for Bash."""

    actions_choices = {
        'default': 'Default action',
        'all': 'Run all actions'
    }
    """List of available installer actions. Actions should be added to this 
    list  as needed."""

    project = 'Default'
    """Script project name."""

    description = 'Installer script for {}.'.format(project)
    """Description of what the script does."""

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter)

    ok_string = '[ \033[1;32m  OK   \033[0m ] '
    warning_string = '[ \033[1;33mWARNING\033[0m ] '
    error_string = '[ \033[1;91m ERROR \033[0m ] '
    unknown_string = '[ \033[1;49mUNKNOWN\033[0m ] '

    @staticmethod
    def yes_no_to_bool(yes_no: str):
        """
        Converts yes or no to bool.
        :param yes_no: Non case sensitive yes/no or y/n.
        :rtype:  bool
        :return: True for yes or false for no.
        :raises: YesNoError
        """
        if yes_no.lower() == 'yes' or yes_no.lower() == 'y':
            return True
        elif yes_no.lower() == 'no' or yes_no.lower() == 'n':
            return False
        raise YesNoError(yes_no)

    # noinspection PyShadowingNames
    def __init__(self, project, script):
        """
        Initializes BashInstall.

        :param project: Project name.
        :param script: Install script name.

        """
        self.first = None
        self.skip = None
        self.cmd_line_args = None

        # Adding variables and values in this dictionary will enable them to be
        # substituted into run_cmd commands
        self.run_cmd_vars = dict()

        # Name of project
        self.run_cmd_vars['PROJECT'] = project
        self.project = project

        # Install script name
        self.run_cmd_vars['SCRIPT'] = script

        # Install script location
        dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.run_cmd_vars['DIR'] = dir

        # Parse command line option
        args = self._parse_command_line_options()
        self.actions = args.actions
        skip = self.skip = args.skip
        no_prompt = args.no_prompt
        self._show_ok = show_ok = args.show_ok
        remote = args.remote
        verbose = args.verbose
        dry_run = args.dry_run
        force_first = args.force_first

        # Set default values according to command line options
        self._mode = 'status'
        if verbose:
            self._mode = 'verbose'
        if dry_run:
            self._mode = 'dry-run'

        # Prompt before running
        if not no_prompt:
            host = 'localhost'
            if remote != "":
                host = remote
            while True:
                try:
                    prompt = self.expand_vars(
                        "Are you sure you want to run {PROJECT} installer on {"
                        "host} (yes/no)? ")
                    yes = self.yes_no_to_bool(input(prompt.format(host=host)))
                    break
                except YesNoError:
                    pass
            if not yes:
                sys.exit(0)

        # Copy program and installer script to remote location and
        # run it there instead
        if remote != "":
            self.run_cmd_vars['REMOTE'] = remote
            self.run_cmd("ssh {REMOTE} 'rm -Rf /tmp/{PROJECT}'",
                         mode='regular')
            self.run_cmd('scp -r {DIR} {REMOTE}:/tmp/{PROJECT}',
                         mode='regular')

            # Run install script on remote side
            opts = ' -p -a ' + ' '.join(args.actions)
            command = "ssh {REMOTE} '/tmp/{PROJECT}/{SCRIPT}{opts}'"
            if skip:
                opts += ' -s'
            if show_ok:
                opts += ' -o'
            if verbose:
                opts += ' -v'
            if force_first:
                opts += ' -f'
            command = command.replace('{opts}', opts)
            self.run_cmd(command, mode='regular')
            sys.exit(0)

        # Set if we are running the script for the first time
        else:
            command = (
                "if [ -f '/var/tmp/{PROJECT}_once' ]; then echo 'true'; fi")
            self.first = self.run_cmd(command, mode='quiet') == 'true'
            if not self.first:
                self.run_cmd('touch /var/tmp/{PROJECT}_once', mode='quiet')
            if force_first:
                self.first = True

    def expand_vars(self, string):
        """
        Expand run command variables in string.

        :param string: Target to expand variables in.
        :rtype:   str
        :returns: String with expanded variables.

        """
        for key, val in self.run_cmd_vars.items():
            var = '{' + key + '}'
            if var in string:
                string = string.replace(var, val)
        return string

    def _fprint(self, string):
        """
        Same as print, but also flushes standard out after print.

        :param string: Target string to print.

        """
        print(self.expand_vars(string))
        sys.stdout.flush()

    def bprint(self, string):
        """
        Same as print but with expanded run variables.

        :param string: Target string to print.

        """
        self._fprint(self.expand_vars(string))

    def path_exists(self, path):
        """
        Same as os.path.exists but with expanded run variables.

        :param path: Target path to test.
        :rtype:   bool
        :returns: If file or folder exists

        """
        return os.path.exists(self.expand_vars(path))

    # noinspection PyShadowingNames,PyUnboundLocalVariable
    def edit_line(self, file_name, regex, replace, mode=None, show_ok=None):
        """
        Edit line in file matching a regular expression.

        :param file_name: Full path and name of file to write content to.
        :param regex:     Regular expression for matching line to edit.
        :param replace:   Replace line with this. Matching groups from regex
                          are matched with {1}...{10}
        :param mode:      Choices are: "status", "regular" and "quiet":
                          "status":  Print command and status.
                          "regular": Print command, stdout and stderr to screen
                                     (just as usual).
                          "verbose": Print status, command, stdout and stderr
                                     to screen.
                          "quiet":   Only print errors.
        :param show_ok:   If ok status should be shown.

        """
        # Set default values
        if mode is None:
            mode = self._mode
        if show_ok is None:
            show_ok = self._show_ok

        error = ''
        # Insert values from run_cmd_vars in "file_name", "regex" and "replace"
        regex = self.expand_vars(regex)
        replace = self.expand_vars(replace)
        file_name = self.expand_vars(file_name)

        # Set OK status message
        status_str = 'Replaced "{old}" with "{replace}" in file "{file_name}"'
        status_str = status_str.replace('{replace}', replace)
        status_str = status_str.replace('{file_name}', file_name)

        # Read file
        try:
            file = open(file_name, 'r', encoding='utf-8')
            line_list = file.readlines()
            line_list = [i.strip('\n') for i in line_list]
            file.close()
        except BaseException as e:
            status_str = 'Error editing file "{file_name}"'
            status_str = status_str.format(file_name=file_name)
            error = str(e)

        # Edit line in file
        if error == '':
            for i in range(len(line_list)):
                match = re.match(pattern=regex, string=line_list[i])

                # Replace line in memory
                if match is not None:
                    # Insert matching groups in replace (if any)
                    for n in range(1, 11):
                        group_string = '{' + str(n) + '}'
                        if group_string in replace:
                            replace = (
                                replace.replace(group_string, match.group(n)))
                    # Complete status string
                    status_str = status_str.format(old=line_list[i])
                    # Replace line in memory
                    line_list[i] = replace
                    break

            # Not finding a match is an error so we set error status
            if match is None:
                status_str = (
                    'No match was found for "{regex}" in "{file_name}"')
                status_str = status_str.format(regex=regex,
                                               file_name=file_name)
                error = None

        # Write file
        if error == '':
            try:
                tmp_file_name = file_name + '~'
                file = open(tmp_file_name, 'w', encoding='utf-8')
                file.writelines('\n'.join(line_list))
                file.close()
                os.rename(tmp_file_name, file_name)
            except BaseException as e:
                status_str = 'Error editing file "{file_name}"'
                status_str = status_str.format(file_name=file_name)
                error = str(e)

        # Print quiet mode
        if mode == 'quiet' and error != '':
            status = '[ \033[1;91mERROR\033[0m ] '
            status_str = status + status_str
            self._fprint(status_str)
            if error is not None:
                self._fprint(error)

        # Print regular mode
        elif mode == 'regular' and (error != '' or show_ok):
            self._fprint(status_str)

        # Print verbose and status mode
        elif (mode == 'verbose' or mode == 'status') and (
                error != '' or show_ok):
            status = '[ \033[1;32m OK  \033[0m ] '
            if error != '':
                status = '[ \033[1;91mERROR\033[0m ] '
            status_str = status + status_str
            self._fprint(status_str)
            if error != '' and error is not None:
                self._fprint(error)

    # noinspection PyShadowingNames
    def write_file(self, file_name, content, mode=None, show_ok=None,
                   file_mode='w'):
        """
        Write content to file.

        :param file_name: Full path and name of file to write content to.
        :param content:   Content to write to file.
        :param mode:      Choices are: "status", "regular" and "quiet":
                          "status":  Print command and status.
                          "regular": Print command, stdout and stderr to screen
                                     (just as usual).
                          "verbose": Print status, command, stdout and stderr
                                     to screen.
                          "quiet":   Only print errors.
        :param show_ok:   If ok status should be shown.
        :param file_mode: Setting this to "w" till overwrite the file.
                          Setting this to "a" till append to the file.

        """
        # Set default values
        if mode is None:
            mode = self._mode
        if show_ok is None:
            show_ok = self._show_ok

        # Insert values from run_cmd_vars in "file_name" and "content"
        file_name = self.expand_vars(file_name)
        content = self.expand_vars(content)

        # Write to file
        error = ''
        status_str = 'Wrote content to "{file_name}"'
        if file_mode == 'a':
            status_str = 'Appended content to "{file_name}"'
        status_str = status_str.format(file_name=file_name)
        try:
            file = open(file_name, file_mode)
            file.write(content)
            file.close()
        except BaseException as e:
            status_str = 'Error writing content to "{file_name}"'
            if file_mode == 'a':
                status_str = 'Error appending content to "{file_name}"'
            status_str = status_str.format(file_name=file_name)
            error = str(e)

        # Print quiet mode
        if mode == 'quiet' and error != '':
            status = '[ \033[1;91mERROR\033[0m ] '
            status_str = status + status_str
            self._fprint(status_str)
            self._fprint(error)

        # Print regular mode
        elif mode == 'regular' and (error != '' or show_ok):
            self._fprint(status_str)

        # Print verbose and status mode
        elif (mode == 'verbose' or mode == 'status') and (
                error != '' or show_ok):
            status = '[ \033[1;32m OK  \033[0m ] '
            if error != '':
                status = '[ \033[1;91mERROR\033[0m ] '
            status_str = status + status_str
            self._fprint(status_str)
            if error != '':
                self._fprint(error)
            elif mode == 'verbose':
                self._fprint(content)

    # noinspection PyShadowingNames,PyTypeChecker,PyUnboundLocalVariable
    def run_cmd(self, command, mode=None, show_ok=None):
        """
        Run a command and print status.

        :param command: Command to run.
        :param mode:    Choices are: "status", "regular" and "quiet":
                        "status":  Print command and status.
                        "regular": Print command, stdout and stderr to screen
                                   (just as usual).
                        "verbose": Print status, command, stdout and stderr to
                                   screen.
                        "quiet":   Only print errors.
        :param show_ok: If ok status should be shown.
        :rtype:   str
        :returns: Target command stdout

        """
        # Set default values
        if mode is None:
            mode = self._mode
        if show_ok is None:
            show_ok = self._show_ok

        # Insert values from run_cmd_vars if they exist
        command = self.expand_vars(command)

        # Handle regular and verbose mode
        if mode.lower() == 'regular' or mode.lower() == 'verbose':
            self._fprint(command)
            error = False
            stdout = ''
            with subprocess.Popen(command,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  bufsize=1,
                                  shell=True,
                                  universal_newlines=True) as p:
                for line in p.stdout:
                    stdout += line
                    print line,
                    sys.stdout.flush()
                for line in p.stderr:
                    error = True
                    print line,
                    sys.stdout.flush()

                    # Print status for verbose mode
            if mode.lower() == 'verbose':
                if error:
                    status = '\033[1;91mERROR\033[0m'
                else:
                    status = '\033[1;32m OK  \033[0m'

                # Print status
                status_str = "[ {status} ] {command}"
                status_str = status_str.format(status=status,
                                               command=command)
                self._fprint(status_str)

            # Return stdout
            return stdout

        # Handle status mode
        elif mode == 'status':
            result = subprocess.run(command, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if result.returncode == 0:
                status = '\033[1;32m OK  \033[0m'
                stderr = ''
            else:
                status = '\033[1;91mERROR\033[0m'
                stderr = '\n' + result.stderr.decode('utf-8')

            # Print status
            if stderr != '' or show_ok:
                status_str = "[ {status} ] {command}{stderr}"
                status_str = status_str.format(status=status,
                                               command=command,
                                               stderr=stderr)
                self._fprint(status_str)

            # Return stdout
            return result.stdout.decode('utf-8')

        # Handle quiet mode
        else:
            result = subprocess.run(command, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

            # Print status if we had an error
            if result.returncode > 0:
                status = '\033[1;91mERROR\033[0m'
                stderr = '\n' + result.stderr.decode('utf-8')
                status_str = "[ {status} ] {command}{stderr}"
                status_str = status_str.format(status=status,
                                               command=command,
                                               stderr=stderr)
                self._fprint(status_str)

            # Return stdout
            return result.stdout.decode('utf-8')

    # noinspection PyShadowingNames
    def _parse_command_line_options(self):
        """
        Parse options from the command line.

        :rtype: Namespace

        """
        action_help = '\n'.join(
            [k+': '+v for k, v in self.actions_choices.items()])
        force_first_help = (
            'Supplying this will run the script as if it was the first time.')
        skip_help = (
            'Supplying this flag will skip as many time consuming steps as '
            'possible to speed up the installation process. This is used for '
            'development purposes only.')
        show_ok_help = 'Supplying this flag will show actions with ok status.'
        verbose_help = 'Supplying this flag will enable all possible output.'
        remote_help = 'Install program on remote user@host.'
        description = (
            'Installer script for the {project}.'.format(project=self.project))
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-a', '--actions', default=['default'], nargs="+",
                            choices=list(self.actions_choices.keys()),
                            help=action_help,
                            required=False)
        parser.add_argument('-f', '--force-first', default=False,
                            action='store_true', help=force_first_help,
                            required=False)
        parser.add_argument('-s', '--skip', default=False, action='store_true',
                            help=skip_help, required=False)
        parser.add_argument('-o', '--show-ok', default=False,
                            action='store_true',
                            help=show_ok_help, required=False)
        parser.add_argument('-v', '--verbose', default=False,
                            action='store_true',
                            help=verbose_help, required=False)
        parser.add_argument('-r', '--remote', type=str, default="",
                            help=remote_help, required=False)
        args = parser.parse_args()

        # Add all actions if "all" is found in action list
        if 'all' in args.actions:
            args.actions = list(self.actions_choices)

        return args
