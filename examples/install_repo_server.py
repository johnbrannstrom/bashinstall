#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. moduleauthor:: John Brännström <john.brannstrom@gmail.com>

Install repository server
*************************

This script will configure a CentOS 8 server as a:
* dnf repository mirror/server.
* pip repository server.

"""

# Built in modules
import os

# Local modules
from bashinst import BashInstall

bash_installer = BashInstall(project='repo_srv',
                             script=os.path.basename(__file__))
run_cmd = bash_installer.run_cmd
write_file = bash_installer.write_file
edit_line = bash_installer.edit_line
first = bash_installer.first
skip = bash_installer.skip
run_cmd_vars = bash_installer.run_cmd_vars

# List of packages to install with dnf
DNF_PACKAGE_LIST = ['httpd', 'python3-pip', 'createrepo', 'yum-utils', 'nano',
                    'mod_ssl', 'createrepo']

# List of packages to install with pip3
PIP3_PACKAGE_LIST = ['python-pypi-mirror']

# Install packages with dnf
if not skip:
    run_cmd('dnf makecache')
    for package in DNF_PACKAGE_LIST:
        run_cmd('dnf -y install {package}'.format(package=package))

# Install packages with pip3
if not skip:
    for package in PIP3_PACKAGE_LIST:
        run_cmd('pip3 install {package}'.format(package=package))

# Create a directory to tore the repositories
run_cmd('mkdir --parents /var/www/repos/centos/8/x86_64/os')
run_cmd('chmod -R 755 /var/www/repos')

# Copy from official repository
if not skip:
    run_cmd('reposync -p /var/www/repos/centos/8/x86_64/os/ '
            '--repo=BaseOS --download-metadata')
    run_cmd('reposync -p /var/www/repos/centos/8/x86_64/os/ '
            '--repo=AppStream --download-metadata')
    run_cmd('reposync -p /var/www/repos/centos/8/x86_64/os/ '
            '--repo=extras --download-metadata')

# Add copy task to daily jobs
content = """#!/bin/bash

VER='8'
ARCH='x86_64'
REPOS=(BaseOS AppStream extras)

for REPO in ${REPOS[@]}
do
    reposync -p /var/www/repos/centos/${VER}/${ARCH}/os/ --repo=${REPO} --download-metadata --newest-only
done
"""
write_file('/etc/cron.daily/update-repo', content)
run_cmd('chmod 755 /etc/cron.daily/update-repo')

# Create custom limited repo
run_cmd('rm -Rf /var/www/repos/centos/8/x86_64/os/limited')
run_cmd('mkdir -p /var/www/repos/centos/8/x86_64/os/limited/Packages')
run_cmd('touch /var/www/repos/centos/8/x86_64/os/limited/mirrorlist')
# Add packages to repo
run_cmd('ln /var/www/repos/centos/8/x86_64/os/BaseOS/Packages/nano-2.9.8-1.el8.x86_64.rpm '
        '/var/www/repos/centos/8/x86_64/os/limited/Packages')
# Run create repository command
run_cmd('createrepo /var/www/repos/centos/8/x86_64/os/limited')

# Create custom limited pip3 repo
run_cmd_vars['PIP3_DIR'] = '/var/www/repos/pip3'
if first:
    run_cmd('ln -s /usr/bin/pip3 /usr/bin/pip')
run_cmd('mkdir -p {PIP3_DIR}')
run_cmd('rm -Rf {PIP3_DIR}/*')
if not skip:
    run_cmd('pypi-mirror download -d {PIP3_DIR}/download pyyaml')
    run_cmd('pypi-mirror download -d {PIP3_DIR}/download requests')
run_cmd('pypi-mirror create -d {PIP3_DIR}/download -m {PIP3_DIR}/simple')
content = """<VirtualHost *:80>
    ServerName pypi.pgcentos1.local

    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI}
</VirtualHost>

<VirtualHost *:443>
    ServerName pypi.pgcentos1.local
    DocumentRoot {PIP3_DIR}/simple

    SSLEngine On
    SSLCertificateFile /etc/pki/tls/certs/pip3.crt
    SSLCertificateKeyFile /etc/pki/tls/private/pip3.key

    <Directory {PIP3_DIR}/>
        AllowOverride None
        Options +Indexes
        IndexOptions SuppressColumnSorting
        IndexIgnore ..
        Order deny,allow
        Allow from all
    </Directory>

    LogLevel warn
    ErrorLog /var/log/httpd/pypi3-error.log
    CustomLog /var/log/httpd/pypi3-access.log combined
</VirtualHost>
"""
write_file('/etc/httpd/conf.d/pypi3.conf', content)


# Configure Apache httpd to provide repository for other Client Hosts
content = """Alias /repos /var/www/repos
<directory /var/www/repos>
    Options +Indexes
    Require all granted
</directory>"""
write_file('/etc/httpd/conf.d/repos.conf', content)
edit_line(file_name='/etc/httpd/conf.d/ssl.conf',
          regex='SSLCertificateFile +.*',
          replace='SSLCertificateFile /etc/pki/tls/certs/dnf.crt')
edit_line(file_name='/etc/httpd/conf.d/ssl.conf',
          regex='SSLCertificateKeyFile +.*',
          replace='SSLCertificateKeyFile /etc/pki/tls/private/dnf.key')
run_cmd('systemctl enable httpd')

# Disable password authentication
if first:
    edit_line(file_name='/etc/ssh/sshd_config',
              regex='PasswordAuthentication +[a-zA-Z0-1]+.*',
              replace='PasswordAuthentication no')
    run_cmd('systemctl restart sshd')

# Allow HTTPS service in firewall
if first:
    run_cmd('firewall-cmd --add-service=https --permanent')
    run_cmd('firewall-cmd --reload')

# Create key and certificate for dnf and then copy both to client
if first:
    run_cmd('openssl genrsa -out /etc/pki/tls/private/dnf.key 2048')
    run_cmd('openssl req -days 3650 -x509 -new -nodes '
            '-key /etc/pki/tls/private/dnf.key -sha256 '
            '-out /etc/pki/tls/certs/dnf.crt '
            '-subj "/C=SE/ST=Östergötland/L=Norrköping/CN=pgcentos1.local"')
    run_cmd('update-ca-trust extract')
    run_cmd('scp /etc/pki/tls/private/dnf.key '
            'root@pgcentos2:/var/lib/dnf/client.key')
    run_cmd('scp /etc/pki/tls/certs/dnf.crt '
            'root@pgcentos2:/var/lib/dnf/client.crt')

# Create key and certificate for pip3 and then copy/add cert to client
if first:
    run_cmd('openssl genrsa -out /etc/pki/tls/private/pip3.key 2048')
    run_cmd('openssl req -days 3650 -x509 -new -nodes '
            '-key /etc/pki/tls/private/pip3.key -sha256 '
            '-out /etc/pki/tls/certs/pip3.crt '
            '-subj "/C=SE/ST=Östergötland/L=Norrköping/CN=pypi.pgcentos1.local"')
    run_cmd('update-ca-trust extract')
    run_cmd('scp /etc/pki/tls/certs/pip3.crt '
            'root@pgcentos2:/etc/pki/ca-trust/source/anchors/pip3.crt')
    run_cmd('ssh root@pgcentos2 "update-ca-trust extract"')

# Activate apache httpd changes
run_cmd('systemctl reload httpd')
run_cmd('systemctl restart httpd')
