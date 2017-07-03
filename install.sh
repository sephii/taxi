#!/bin/sh
# This install script is taken from Lektor (https://www.getlektor.com/) by
# Armin Ronacher, and released under the BSD license. It has been adapted to
# run on Python 3 as well as on Python 2.
#
# Copyright (c) 2015 by the Armin Ronacher.
#
# Some rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * The names of the contributors may not be used to endorse or
#       promote products derived from this software without specific
#       prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Wrap everything in a function so that we do not accidentally execute
# something we should not in case a truncated version of the script
# is executed.
I() {
  set -u

  if hash python3 2> /dev/null; then
    PY=python3
  elif hash python 2> /dev/null; then
    PY=python
  else
    echo "Error: To use this script you need to have Python installed"
    exit 1
  fi

  $PY - <<'EOF'
if 1:

    import os
    import sys
    import json
    import urllib
    import tempfile
    import shutil
    from subprocess import Popen

    PY3 = sys.version_info[0] == 3
    input_func = raw_input if not PY3 else input

    if PY3:
        from urllib.request import urlopen
    else:
        from urllib import urlopen

    sys.stdin = open('/dev/tty', 'r')

    VENV_URL = "https://pypi.python.org/pypi/virtualenv/json"
    KNOWN_BINS = ['/usr/local/bin', '/opt/local/bin',
                  os.path.join(os.environ['HOME'], '.bin'),
                  os.path.join(os.environ['HOME'], '.local', 'bin')]

    def abort():
        print('')
        print('Aborted!')
        sys.exit()

    def find_user_paths():
        rv = []
        for item in os.environ['PATH'].split(':'):
            if os.access(item, os.W_OK) \
               and item not in rv \
               and '/sbin' not in item:
                rv.append(item)
        return rv

    def bin_sort_key(path):
        try:
            return KNOWN_BINS.index(path)
        except ValueError:
            return float('inf')

    def find_locations(paths):
        paths.sort(key=bin_sort_key)
        for path in paths:
            if path.startswith(os.environ['HOME']):
                return path, os.path.join(os.environ['HOME'],
                    '.local', 'lib', 'taxi')
            elif path.endswith('/bin'):
                return path, os.path.join(
                    os.path.dirname(path), 'lib', 'taxi')
        None, None

    def get_confirmation(message="Continue?"):
        while 1:
            user_input = input_func(message + ' [Yn] ').lower().strip()
            if user_input in ('', 'y'):
                return True
            elif user_input == 'n':
                return False

    def wipe_installation(lib_dir, symlink_path):
        if os.path.lexists(symlink_path):
            os.remove(symlink_path)
        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir, ignore_errors=True)

    def check_installation(lib_dir, bin_dir):
        symlink_path = os.path.join(bin_dir, 'taxi')
        if os.path.exists(lib_dir) or os.path.lexists(symlink_path):
            print('   Taxi seems to be installed already.')
            print('   Continuing will wipe %s and remove %s' % (lib_dir, symlink_path))
            print('')
            if not get_confirmation():
                abort()
            print('')
            wipe_installation(lib_dir, symlink_path)

    def fail(message):
        print('Error: %s' % message)
        sys.exit(1)

    def install(virtualenv_url, lib_dir, bin_dir):
        t = tempfile.mkdtemp()
        Popen('curl -sf "%s" | tar -xzf - --strip-components=1' %
              virtualenv_url, shell=True, cwd=t).wait()

        try:
            os.makedirs(lib_dir)
        except OSError:
            pass
        Popen([sys.executable, './virtualenv.py', lib_dir], cwd=t).wait()
        Popen([os.path.join(lib_dir, 'bin', 'pip'),
           'install', '--upgrade', 'taxi'], env={}).wait()
        os.symlink(os.path.join(lib_dir, 'bin', 'taxi'),
                   os.path.join(bin_dir, 'taxi'))

    def main():
        print('')
        print('Welcome to Taxi')
        print('')
        print('This script will install Taxi on your computer.')
        print('')

        paths = find_user_paths()
        if not paths:
            fail('None of the items in $PATH are writable. Run with '
                 'sudo or add a $PATH item that you have access to.')

        bin_dir, lib_dir = find_locations(paths)
        if bin_dir is None or lib_dir is None:
            fail('Could not determine installation location for Taxi.')

        check_installation(lib_dir, bin_dir)

        print('Installing at:')
        print('  bin: %s' % bin_dir)
        print('  app: %s' % lib_dir)
        print('')

        if not get_confirmation():
            abort()

        venv_contents = urlopen(VENV_URL).read()

        if PY3:
            venv_contents = venv_contents.decode('utf-8')

        for url in json.loads(venv_contents)['urls']:
            if url['python_version'] == 'source':
                virtualenv = url['url']
                break
        else:
            fail('Could not find virtualenv')

        install(virtualenv, lib_dir, bin_dir)

        print('')
        if get_confirmation("Do you plan to use Taxi with Zebra?"):
            Popen([os.path.join(lib_dir, 'bin', 'pip'), 'install',
                  'taxi-zebra'], env={}).wait()

        print('')
        print("Taxi has been installed successfully! You can now run 'taxi"
              " update' to run the configuration setup and fetch your projects"
              " list.")
        print('')

    main()
EOF
}

I
