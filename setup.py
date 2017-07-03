#!/usr/bin/env python
from setuptools import find_packages, setup

from taxi import __version__

tests_require = [
    'freezegun>=0.2.8',
    'pytest>=2.7.3',
]

install_requires = [
    'click>=3.3',
    'six>=1.9.0',
    'appdirs>=1.4.0',
]


setup(
    name='taxi',
    version=__version__,
    packages=find_packages(exclude=('tests', 'tests.*')),
    description='Taxi: timesheeting made easy',
    author='Sylvain Fankhauser',
    author_email='sylvain.fankhauser@liip.ch',
    url='https://github.com/sephii/taxi',
    install_requires=install_requires,
    setup_requires=['pytest-runner'],
    license='wtfpl',
    tests_require=tests_require,
    include_package_data=False,
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
        'Programming Language :: Python :: 3.5',
    ]
)
