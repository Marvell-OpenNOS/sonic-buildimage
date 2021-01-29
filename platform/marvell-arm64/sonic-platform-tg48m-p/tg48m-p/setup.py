#!/usr/bin/env python

import os
from setuptools import setup
os.listdir

setup(
   name='sonic_platform',
   version='1.0',
   description='Module to initialize Delta TG48M-P platforms',

   packages=['sonic_platform','sonic_platform.test'],
   package_dir={'sonic_platform': 'tg48m-p/sonic_platform'},
)

