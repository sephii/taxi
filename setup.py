#!/usr/bin/env python
from setuptools import find_packages, setup
import sys
from taxi import __version__

from setuptools.command.test import test as TestCommand


tests_require = [
    'freezegun==0.2.2',
    'mock==1.0.1',
    'pytest==2.6.4',
]

install_requires = [
    'colorama>=0.3.1'
]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='taxi',
    version=__version__,
    packages=find_packages(exclude=('tests', 'tests.*')),
    description='Taxi is a Zebra frontend',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    scripts=['bin/taxi'],
    url='https://github.com/sephii/taxi',
    install_requires=install_requires,
    license='wtfpl',
    tests_require=tests_require,
    include_package_data=False,
    cmdclass = {'test': PyTest},
    package_data={
        'taxi': ['doc/*']
    }
)
