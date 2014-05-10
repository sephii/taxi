#!/usr/bin/env python
from setuptools import find_packages, setup
from taxi import __version__

tests_require = [
    'freezegun',
    'mock',
]


setup(
    name='taxi',
    version=__version__,
    packages=find_packages(exclude=('tests', 'tests.*')),
    description='Taxi is a Zebra frontend',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    scripts=['bin/taxi'],
    url='https://github.com/sephii/taxi',
    tests_require=tests_require,
    test_suite='tests.runtests.suite',
    include_package_data=False
)
