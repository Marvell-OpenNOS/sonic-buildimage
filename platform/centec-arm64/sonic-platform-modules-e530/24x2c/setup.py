#!/usr/bin/env python

import os
from setuptools import setup
os.listdir

setup(
   name='sonic_platform',
   version='1.0',
   description='Module to initialize centec e530-24x2c platforms',
   
   packages=['sonic_platform'],
   package_dir={'sonic_platform': 'sonic_platform'},
)

