#!/usr/bin/env python
from distutils.core import setup

setup(
    name='taxi',
    version='2.2',
    packages=['taxi'],
    package_dir={'taxi': 'src/taxi'},
    description='Taxi is a Zebra frontend',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    scripts = ['taxi'],
)
