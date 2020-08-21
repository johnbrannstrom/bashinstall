#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. moduleauthor:: John Brännström <john.brannstrom@gmail.com>

Install CentOS 8 client
***********************

This script will configure a CentOS 8 server as a Dnf repository client.

"""

# Built in modules
import subprocess
import argparse
import os
import sys
import re


# Adding variables and values in this dictionary will enable them to be
# substituted into run_cmd commands
run_cmd_vars = dict()

# Name of project
PROJECT = 'dnf_client'
run_cmd_vars['PROJECT'] = PROJECT

# Install script location
run_cmd_vars['DIR'] = os.path.dirname(os.path.realpath(sys.argv[0]))

# Install script name
run_cmd_vars['SCRIPT'] = os.path.basename(__file__)


# noinspection PyShadowingNames,PyUnboundLocalVariable
def edit_line(file_name: str, regex: str, replace: str, mode: str = 'status',
              show_ok: bool = False):
    """
    Edit line in file matching a regular expression.

    :param file_name: Full path and name of file to write content to.
    :param regex:     Regular expression for matching line to edit.
    :param replace:   Replace line with this. Matching groups from regex are
                      matched with {1}...{10}
    :param mode:      Choices are: "status", "regular" and "quiet":
                      "status":  Print command and status.
                      "regular": Print command, stdout and stderr to screen
                                 (just as usual).
                      "verbose": Print status, command, stdout and stderr to
                                 screen.
                      "quiet":   Only print errors.
    :param show_ok:   If ok status should be shown.

    """
    error = ''
    # Insert values from run_cmd_vars in "regex" and "replace"
    # (if they exist)
    for key, val in run_cmd_vars.items():
        var = '{' + key + '}'
        if var in regex:
            regex = regex.replace(var, val)
        if var in replace:
            replace = replace.replace(var, val)

    # Set OK status message
    status_string = 'Replaced "{old}" with "{replace}" in file "{file_name}"'
    status_string = status_string.replace('{replace}', replace)
    status_string = status_string.replace('{file_name}', file_name)

    # Read file
    try:
        file = open(file_name, 'r', encoding='utf-8')
        line_list = file.readlines()
        line_list = [i.strip('\n') for i in line_list]
        file.close()
    except BaseException as e:
        status_string = 'Error editing file "{file_name}"'
        status_string = status_string.format(file_name=file_name)
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
                        replace = replace.replace(group_string, match.group(n))
                # Complete status string
                status_string = status_string.format(old=line_list[i])
                # Replace line in memory
                line_list[i] = replace
                break

        # Not finding a match is an error so we set error status
        if match is None:
            status_string = 'No match was found for "{regex}" in "{file_name}"'
            status_string = status_string.format(regex=regex,
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
            status_string = 'Error editing file "{file_name}"'
            status_string = status_string.format(file_name=file_name)
            error = str(e)

    # Print quiet mode
    if mode == 'quiet' and error != '':
        status = '[ \033[1;91mERROR\033[0m ] '
        status_string = status + status_string
        print(status_string, flush=True)
        if error is not None:
            print(error, flush=True)

    # Print regular mode
    elif mode == 'regular' and (error != '' or show_ok):
        print(status_string, flush=True)

    # Print verbose and status mode
    elif (mode == 'verbose' or mode == 'status') and (error != '' or show_ok):
        status = '[ \033[1;32m OK  \033[0m ] '
        if error != '':
            status = '[ \033[1;91mERROR\033[0m ] '
        status_string = status + status_string
        print(status_string, flush=True)
        if error != '' and error is not None:
            print(error, flush=True)


# noinspection PyShadowingNames
def write_file(file_name: str, content: str, mode: str = 'status',
               show_ok: bool = False, file_mode: str = 'w'):
    """
    Write content to file.

    :param file_name: Full path and name of file to write content to.
    :param content:   Content to write to file.
    :param mode:      Choices are: "status", "regular" and "quiet":
                      "status":  Print command and status.
                      "regular": Print command, stdout and stderr to screen
                                 (just as usual).
                      "verbose": Print status, command, stdout and stderr to
                                 screen.
                      "quiet":   Only print errors.
    :param show_ok:   If ok status should be shown.
    :param file_mode: Setting this to "w" till overwrite the file.
                      Setting this to "a" till append to the file.

    """
    # Insert values from run_cmd_vars in "file_name" and "content"
    # (if they exist)
    for key, val in run_cmd_vars.items():
        var = '{' + key + '}'
        if var in file_name:
            file_name = file_name.replace(var, val)
        if var in content:
            content = content.replace(var, val)

    # Write to file
    error = ''
    status_string = 'Wrote content to "{file_name}"'
    if file_mode == 'a':
        status_string = 'Appended content to "{file_name}"'
    status_string = status_string.format(file_name=file_name)
    try:
        file = open(file_name, file_mode)
        file.write(content)
        file.close()
    except BaseException as e:
        status_string = 'Error writing content to "{file_name}"'
        if file_mode == 'a':
            status_string = 'Error appending content to "{file_name}"'
        status_string = status_string.format(file_name=file_name)
        error = str(e)

    # Print quiet mode
    if mode == 'quiet' and error != '':
        status = '[ \033[1;91mERROR\033[0m ] '
        status_string = status + status_string
        print(status_string, flush=True)
        print(error, flush=True)

    # Print regular mode
    elif mode == 'regular' and (error != '' or show_ok):
        print(status_string, flush=True)

    # Print verbose and status mode
    elif (mode == 'verbose' or mode == 'status') and (error != '' or show_ok):
        status = '[ \033[1;32m OK  \033[0m ] '
        if error != '':
            status = '[ \033[1;91mERROR\033[0m ] '
        status_string = status + status_string
        print(status_string, flush=True)
        if error != '':
            print(error, flush=True)
        elif mode == 'verbose':
            print(content, flush=True)


# noinspection PyShadowingNames,PyTypeChecker,PyUnboundLocalVariable
def run_cmd(command: str, mode: str = 'status', show_ok: bool = False):
    """
    Run a command and print status.

    :param command: Command to run.
    :param mode:    Choices are: "status", "regular" and "quiet":
                    "status":  Print command and status.
                    "regular": Print command, stdout and stderr to screen (just
                               as usual).
                    "verbose": Print status, command, stdout and stderr to
                               screen.
                    "quiet":   Only print errors.
    :param show_ok: If ok status should be shown.

    """
    # Insert values from run_cmd_vars if they exist
    for key, val in run_cmd_vars.items():
        var = '{' + key + '}'
        if var in command:
            command = command.replace(var, val)

    # Handle regular and verbose mode
    if mode.lower() == 'regular' or mode.lower() == 'verbose':
        print(command, flush=True)
        error = False
        with subprocess.Popen(command,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              bufsize=1,
                              shell=True,
                              universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='', flush=True)
            for line in p.stderr:
                error = True
                print(line, end='', flush=True)
        # Print status for verbose mode
        if mode.lower() == 'verbose':
            if error:
                status = '\033[1;91mERROR\033[0m'
            else:
                status = '\033[1;32m OK  \033[0m'

            # Print status
            status_string = "[ {status} ] {command}"
            status_string = status_string.format(status=status,
                                                 command=command)
            print(status_string, flush=True)

    # Handle status mode
    elif mode == 'status':
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if result.returncode == 0:
            status = '\033[1;32m OK  \033[0m'
            stderr = ''
        else:
            status = '\033[1;91mERROR\033[0m'
            stderr = '\n' + result.stderr.decode('utf-8')

        # Print status
        if stderr != '' or show_ok:
            status_string = "[ {status} ] {command}{stderr}"
            status_string = status_string.format(status=status,
                                                 command=command,
                                                 stderr=stderr)
            print(status_string, flush=True)

    # Handle quiet mode
    else:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        # Print status if we had an error
        if result.returncode > 0:
            status = '\033[1;91mERROR\033[0m'
            stderr = '\n' + result.stderr.decode('utf-8')
            status_string = "[ {status} ] {command}{stderr}"
            status_string = status_string.format(status=status,
                                                 command=command,
                                                 stderr=stderr)
            print(status_string, flush=True)


# Parse command line arguments
# noinspection PyShadowingNames
def parse_command_line_options():
    """
    Parse options from the command line.
    
    :rtype: Namespace

    """
    skip_help = (
        'Supplying this flag will skip as many time consuming steps as possibl'
        'e to speed up the installation process. This is used for development '
        'purposes only.')
    show_ok_help = 'Supplying this flag will also actions with show ok status.'
    verbose_help = 'Supplying this flag will enable all possible output.'
    remote_help = 'Install program on remote user@host.'
    description = 'Installer script for the {PROJECT}.'.format(PROJECT=PROJECT)
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--skip', default=False, action='store_true',
                        help=skip_help, required=False)
    parser.add_argument('-o', '--show-ok', default=False, action='store_true',
                        help=show_ok_help, required=False)
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help=verbose_help, required=False)
    parser.add_argument('-r', '--remote', type=str, default="",
                        help=remote_help, required=False)
    args = parser.parse_args()
    return args


args = parse_command_line_options()
skip = args.skip
show_ok = args.show_ok
remote = args.remote
verbose = args.verbose

# Set default values according to command line options
mode = 'status'
if verbose:
    mode = 'verbose'
run_cmd.__defaults__ = (None, mode, show_ok)
write_file.__defaults__ = (None, None, mode, show_ok, 'w')
edit_line.__defaults__ = (None, None, None, mode, show_ok)

# Copy program and installer script to remote location and run it there instead
if remote != "":
    run_cmd_vars['REMOTE'] = remote
    run_cmd("ssh {REMOTE} 'mkdir -p /tmp/{PROJECT}'", mode='quiet')
    run_cmd("echo 'put -r {DIR}/*' > /tmp/sftp_batchfile", mode='quiet')
    run_cmd("sftp -b /tmp/sftp_batchfile {REMOTE}:/tmp/{PROJECT}",
            mode='regular')
    run_cmd("rm /tmp/sftp_batchfile", mode='quiet')

    # Run install script on remote side
    opts = ''
    command = "ssh {REMOTE} '/tmp/{PROJECT}/{SCRIPT}{opts}'"
    if skip:
        opts += ' -s'
    if show_ok:
        opts += ' -o'
    if verbose:
        opts += ' -v'
    command = command.replace('{opts}', opts)
    run_cmd(command, mode='regular')
    sys.exit(0)

# Add program specific content below this line

# List of packages to install with dnf
DNF_PACKAGE_LIST = ['nano']

# List of packages to install with pip3
PIP3_PACKAGE_LIST = []

# Install packages with dnf
if not skip:
    run_cmd('dnf makecache')
    for package in DNF_PACKAGE_LIST:
        run_cmd('dnf -y install {package}'.format(package=package))

# Install packages with pip3
if not skip:
    for package in PIP3_PACKAGE_LIST:
        run_cmd('pip3 install {package}'.format(package=package))

# Change settings of dnf to refer to Local dnf Mirror Host
content = """[BaseOS]
name=CentOS-$releasever - Base
baseurl=https://pgcentos1.local/repos/centos/$releasever/$basearch/os/BaseOS/
gpgcheck=1
enabled=1
gpgkey=https://pgcentos1.local/RPM-GPG-KEY

sslverify=1
sslclientcert=/var/lib/dnf/client.crt
sslclientkey=/var/lib/dnf/client.key"""
write_file('/etc/yum.repos.d/CentOS-Base.repo', content)

content = """[AppStream]
name=CentOS-$releasever - AppStream
baseurl=https://pgcentos1.local/repos/centos/$releasever/$basearch/os/AppStream/
gpgcheck=1
enabled=1
gpgkey=https://pgcentos1.local/RPM-GPG-KEY

sslverify=1
sslclientcert=/var/lib/dnf/client.crt
sslclientkey=/var/lib/dnf/client.key"""
write_file('/etc/yum.repos.d/CentOS-Extras.repo', content)

content = """[extras]
name=CentOS-$releasever - Extras
baseurl=https://pgcentos1.local/repos/centos/$releasever/$basearch/os/extras/
gpgcheck=1
enabled=1
gpgkey=https://pgcentos1.local/RPM-GPG-KEY

sslverify=1
sslclientcert=/var/lib/dnf/client.crt
sslclientkey=/var/lib/dnf/client.key"""
write_file('/etc/yum.repos.d/CentOS-Extras.repo', content)

# Add local pip repo for root user
if not skip:
    content ="""[global]
; Extra index to private pypi dependencies
index-url = https://pypi.pgcentos1.local
trusted-host = pypi.pgcentos1.local
"""
    write_file('/root/.pip/pip.conf', content)

# Generate
if not skip:
    print()
    print('The following needs to be done manually:')
    print('Place client key here: /var/lib/dnf/client.key')
    print('Place client cert here: /var/lib/dnf/client.crt')
