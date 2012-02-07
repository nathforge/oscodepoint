#!/usr/bin/env python

from setuptools import setup
import os
import sys

PACKAGE_PATH = 'src'

setup(
    name='oscodepoint',
    url='https://github.com/nathforge/oscodepoint',
    version='0.1',
    description='A Python interface to Ordnance Survey\'s CodePoint-Open data',
    long_description=open('README.txt').read(),
    
    author='Nathan Reynolds',
    author_email='email@nreynolds.co.uk',
    
    packages=['oscodepoint'],
    package_dir={'': PACKAGE_PATH},

    install_requires=[
        'pyproj',
        'xlrd',
    ],
)
