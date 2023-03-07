#!/usr/bin/env python
from setuptools import find_packages, setup

from taxi import __version__

install_requires = [
    'click>=3.3',
    'appdirs>=1.4.0',
]


setup(
    name='taxi',
    version=__version__,
    packages=find_packages(exclude=('tests', 'tests.*')),
    description='Taxi: timesheeting made easy',
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    url='https://github.com/liip/taxi',
    install_requires=install_requires,
    license='wtfpl',
    include_package_data=False,
    package_data={
        'taxi': ['etc/*']
    },
    python_requires=">=3.5",
    entry_points={
        'taxi.backends': 'dummy = taxi.backends.dummy:DummyBackend',
        'console_scripts': 'taxi = taxi.commands.base:cli'
    },
    classifiers=[
        'Environment :: Console',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
