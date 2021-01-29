#!/usr/bin/env python

import sys
import os.path
if sys.version_info[0] < 3:
    import commands as cmd
else:
    import subprocess as cmd

smbus_present = 1
try:
   import smbus
except ImportError as e:
   smbus_present = 0 

try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
       PsuBase.__init__(self)
       MAX_PSUS = 2

    def get_num_psus(self):
        MAX_PSUS = 2
        return MAX_PSUS

    def get_psu_status(self, index):
        if index is None:
           return False
        if smbus_present == 0: 
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 2 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if index == 1:
            psustatus = psustatus&4
            if psustatus == 4 :
               return True
        if index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
               return True
                    
        return False

    def get_psu_presence(self, index):
        if index is None:
            return False

        if smbus_present == 0: 
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 2 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if index == 1:
             psustatus = psustatus&1
             if psustatus == 0 :
                 return True
        if index == 2:
            psustatus = psustatus&2
            if psustatus == 0 :
                return True
        return False

