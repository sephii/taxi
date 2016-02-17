#!/usr/bin/env python
from setuptools import find_packages, setup
import sys
from taxi import __version__

from setuptools.command.test import test as TestCommand


tests_require = [
    'freezegun==0.2.8',
    'pytest==2.7.0',
]

install_requires = [
    'click>=3.3',
    'six>=1.9.0',
    'appdirs>=1.4.0',
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
    description='Taxi: timesheeting made easy',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    url='https://github.com/sephii/taxi',
    install_requires=install_requires,
    license='wtfpl',
    tests_require=tests_require,
    include_package_data=False,
    cmdclass = {'test': PyTest},
    package_data={
        'taxi': ['etc/*']
    },
    entry_points={
        'taxi.backends': 'dummy = taxi.backends.dummy:DummyBackend',
        'console_scripts': 'taxi = taxi.commands.base:cli'
    },
    classifiers=[
        'Environment :: Console',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ]
)
