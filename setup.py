#!/usr/bin/env python
from distutils.core import setup

setup(
    name='taxi',
    version='1.0',
    #py_modules=['taxi'],
    packages=['taxi'],
    package_dir={'taxi': 'src/taxi'},
    description='Taxi is a Zebra frontend',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    scripts = ['taxi'],
)
