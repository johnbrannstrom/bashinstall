#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. moduleauthor:: John Brännström <john.brannstrom@gmail.com>

Install showcase
****************

This script is a showcase of what can be done with bash install.

"""

# Built in modules
import os

# Local modules
from bashinst import BashInstall

# Init Bash installer
BashInstall.actions_choices.update({
    'custom_option': 'Custom option added for specific installer.'
})
custom_arg_help = 'Extra custom argument.'
BashInstall.add_argument('--custom-arg1', default='value1', type=str,
                         help=custom_arg_help, required=False)
BashInstall.prompt_default = True
BashInstall.show_ok_default = True
BashInstall.remote_required = False
bash_installer = BashInstall(script=os.path.basename(__file__),
                             project='showcase',
                             description='Bash install showcase script.')
run_cmd = bash_installer.run_cmd
write_file = bash_installer.write_file
edit_line = bash_installer.edit_line
bprint = bash_installer.bprint
expand_vars = bash_installer.expand_vars
first = bash_installer.first
skip = bash_installer.skip
verbose = bash_installer.verbose
actions = bash_installer.actions
run_cmd_vars = bash_installer.run_cmd_vars
cmd_line_args = bash_installer.cmd_line_args

# Test default action
if 'default' in actions:
    run_cmd('echo "Testing default action"')

# Print variable values
if 'default' in actions:
    bprint("The value of PROJECT is: {PROJECT}")
    bprint("The value of SCRIPT is: {SCRIPT}")
    bprint("The value of DIR is: {DIR}")
    bprint("The value of UUID is: {UUID}")
    bprint("The value of CUSTOM_ARG1 is: {CUSTOM_ARG1}")

# Print value of custom argument
if 'default' in actions:
    bprint(cmd_line_args.custom_arg1)

# Test default action and first
if 'default' in actions and first:
    run_cmd('echo "Testing default action and first"')

# Test error status
if 'default' in actions:
    run_cmd('not_a_command')

# Test warning status
if 'default' in actions:
    run_cmd('not_a_command', warning=True)

# Test writing to file
if 'default' in actions:
    write_file('/tmp/bash_install_test_file', 'next_line_1\ntest_line_2\n')

# Test writing to file error
if 'default' in actions:
    write_file('/9786sadg872613gcasdh987ygh/bash_install_test_file',
               'next_line_1\ntest_line_2\n')

# Test writing to file warning
if 'default' in actions:
    write_file('/9786sadg872613gcasdh987ygh/bash_install_test_file', '',
               warning=True)

# Test default action
if 'default' in actions:
    run_cmd('echo "Testing default action"')

# Test edit line success
if 'default' in actions:
    edit_line('/tmp/bash_install_test_file',
              regex='.*_1', replace='replaced_1')

# Test edit line fail
if 'default' in actions:
    edit_line('/tmp/bash_install_test_file',
              regex='uhsdf786sdt', replace='replaced_1')

# Test edit line warning
if 'default' in actions:
    edit_line('/tmp/bash_install_test_file',
              regex='uhsdf786sdt', replace='replaced_1', warning=True)
