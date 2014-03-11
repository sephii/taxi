#!/usr/bin/env python
from setuptools import setup
from taxi import __version__

setup(
    name='taxi',
    version=__version__,
    packages=['taxi', 'taxi.utils', 'taxi.parser', 'taxi.parser.parsers',
              'taxi.ui'],
    description='Taxi is a Zebra frontend',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    scripts = ['bin/taxi'],
    url='https://github.com/sephii/taxi',
)
