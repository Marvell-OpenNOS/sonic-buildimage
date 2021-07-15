#!/usr/bin/env python
'''
listen to the SDK for the SFP change event and return to chassis.
'''

from __future__ import print_function
import os
import time
from sonic_py_common import logger

smbus_present = 1

try:
    import smbus
except ImportError as e:
    smbus_present = 0

profile_16x400G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,4",   5:"0x70,4",   6:"0x70,4",   7:"0x70,4",
  8:"0x70,5",   9:"0x70,5",  10:"0x70,5",  11:"0x70,5",  12:"0x70,5",  13:"0x70,5",  14:"0x70,5",  15:"0x70,5",
 16:"0x70,6",  17:"0x70,6",  18:"0x70,6",  19:"0x70,6",  20:"0x70,6",  21:"0x70,6",  22:"0x70,6",  23:"0x70,6",
 24:"0x70,7",  25:"0x70,7",  26:"0x70,7",  27:"0x70,7",  28:"0x70,7",  29:"0x70,7",  30:"0x70,7",  31:"0x70,7",
 32:"0x70,0",  33:"0x70,0",  34:"0x70,0",  35:"0x70,0",  36:"0x70,0",  37:"0x70,0",  38:"0x70,0",  39:"0x70,0",
 40:"0x70,1",  41:"0x70,1",  42:"0x70,1",  43:"0x70,1",  44:"0x70,1",  45:"0x70,1",  46:"0x70,1",  47:"0x70,1",
 48:"0x70,2",  49:"0x70,2",  50:"0x70,2",  51:"0x70,2",  52:"0x70,2",  53:"0x70,2",  54:"0x70,2",  55:"0x70,2",
 56:"0x70,3",  57:"0x70,3",  58:"0x70,3",  59:"0x70,3",  60:"0x70,3",  61:"0x70,3",  62:"0x70,3",  63:"0x70,3",
 64:"0x71,4",  65:"0x71,4",  66:"0x71,4",  67:"0x71,4",  68:"0x71,4",  69:"0x71,4",  70:"0x71,4",  71:"0x71,4",
 72:"0x71,5",  73:"0x71,5",  74:"0x71,5",  75:"0x71,5",  76:"0x71,5",  77:"0x71,5",  78:"0x71,5",  79:"0x71,5",
 80:"0x71,6",  81:"0x71,6",  82:"0x71,6",  83:"0x71,6",  84:"0x71,6",  85:"0x71,6",  86:"0x71,6",  87:"0x71,6",
 88:"0x71,7",  89:"0x71,7",  90:"0x71,7",  91:"0x71,7",  92:"0x71,7",  93:"0x71,7",  94:"0x71,7",  95:"0x71,7",
 96:"0x71,0",  97:"0x71,0",  98:"0x71,0",  99:"0x71,0", 100:"0x71,0", 101:"0x71,0", 102:"0x71,0", 103:"0x71,0",
104:"0x71,1", 105:"0x71,1", 106:"0x71,1", 107:"0x71,1", 108:"0x71,1", 109:"0x71,1", 110:"0x71,1", 111:"0x71,1",
112:"0x71,2", 113:"0x71,2", 114:"0x71,2", 115:"0x71,2", 116:"0x71,2", 117:"0x71,2", 118:"0x71,2", 119:"0x71,2",
120:"0x71,3", 121:"0x71,3", 122:"0x71,3", 123:"0x71,3", 124:"0x71,3", 125:"0x71,3", 126:"0x71,3", 127:"0x71,3",
128:"0x74,4", 129:"0x74,5" }

profile_64x25G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,5",   5:"0x70,5",   6:"0x70,5",   7:"0x70,5",
  8:"0x70,6",   9:"0x70,6",  10:"0x70,6",  11:"0x70,6",  12:"0x70,7",  13:"0x70,7",  14:"0x70,7",  15:"0x70,7",
 16:"0x70,0",  17:"0x70,0",  18:"0x70,0",  19:"0x70,0",  20:"0x70,1",  21:"0x70,1",  22:"0x70,1",  23:"0x70,1",
 24:"0x70,2",  25:"0x70,2",  26:"0x70,2",  27:"0x70,2",  28:"0x70,3",  29:"0x70,3",  30:"0x70,3",  31:"0x70,3",
 32:"0x71,4",  33:"0x71,4",  34:"0x71,4",  35:"0x71,4",  36:"0x71,5",  37:"0x71,5",  38:"0x71,5",  39:"0x71,5",
 40:"0x71,6",  41:"0x71,6",  42:"0x71,6",  43:"0x71,6",  44:"0x71,7",  45:"0x71,7",  46:"0x71,7",  47:"0x71,7",
 48:"0x71,0",  49:"0x71,0",  50:"0x71,0",  51:"0x71,0",  52:"0x71,1",  53:"0x71,1",  54:"0x71,1",  55:"0x71,1",
 56:"0x71,2",  57:"0x71,2",  58:"0x71,2",  59:"0x71,2",  60:"0x71,3",  61:"0x71,3",  62:"0x71,3",  63:"0x71,3",
 64:"0x74,4",  65:"0x74,5" }

profile_32x25G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,5",   3:"0x70,5",   4:"0x70,6",   5:"0x70,6",   6:"0x70,7",   7:"0x70,7",
  8:"0x70,0",   9:"0x70,0",  10:"0x70,1",  11:"0x70,1",  12:"0x70,2",  13:"0x70,2",  14:"0x70,3",  15:"0x70,3",
 16:"0x71,4",  17:"0x71,4",  18:"0x71,5",  19:"0x71,5",  20:"0x71,6",  21:"0x71,6",  22:"0x71,7",  23:"0x71,7",
 24:"0x71,0",  25:"0x71,0",  26:"0x71,1",  27:"0x71,1",  28:"0x71,2",  29:"0x71,2",  30:"0x71,3",  31:"0x71,3",
 32:"0x74,4",  33:"0x74,5" }

profile_16x25G = {
 0:"0x70,4",   1:"0x70,5",   2:"0x70,6",   3:"0x70,7",   4:"0x70,0",   5:"0x70,1",   6:"0x70,2",   7:"0x70,3",
 8:"0x71,4",   9:"0x71,5",  10:"0x71,6",  11:"0x71,7",  12:"0x71,0",  13:"0x71,1",  14:"0x71,2",  15:"0x71,3",
16:"0x74,4",  17:"0x74,5" }

profile_16x25G_ixia = {
 0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,5",   5:"0x70,5",   6:"0x70,5",   7:"0x70,5",
 8:"0x70,6",   9:"0x70,6",  10:"0x70,6",  11:"0x70,6",  12:"0x70,7",  13:"0x70,7",  14:"0x70,7",  15:"0x70,7",
16:"0x74,4",  17:"0x74,5" }

profile_24x25G_4x200G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,5",   3:"0x70,5",   4:"0x70,6",   5:"0x70,6",   6:"0x70,7",   7:"0x70,7",
  8:"0x70,0",   9:"0x70,0",  10:"0x70,1",  11:"0x70,1",  12:"0x70,2",  13:"0x70,2",  14:"0x70,3",  15:"0x70,3",
 16:"0x71,4",  17:"0x71,4",  18:"0x71,5",  19:"0x71,5",  20:"0x71,6",  21:"0x71,6",  22:"0x71,7",  23:"0x71,7",
 24:"0x71,0",  25:"0x71,0",  26:"0x71,0",  27:"0x71,0",  28:"0x71,1",  29:"0x71,1",  30:"0x71,1",  31:"0x71,1",
 32:"0x71,2",  33:"0x71,2",  34:"0x71,2",  35:"0x71,2",  36:"0x71,3",  37:"0x71,3",  38:"0x71,3",  39:"0x71,3",
 40:"0x74,4",  41:"0x74,5" }

profile_24x25G_8x200G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,5",   3:"0x70,5",   4:"0x70,6",   5:"0x70,6",   6:"0x70,7",   7:"0x70,7",
  8:"0x70,0",   9:"0x70,0",  10:"0x70,1",  11:"0x70,1",  12:"0x70,2",  13:"0x70,2",  14:"0x70,3",  15:"0x70,3",
 16:"0x71,4",  17:"0x71,4",  18:"0x71,5",  19:"0x71,5",  20:"0x71,6",  21:"0x71,6",  22:"0x71,7",  23:"0x71,7",
 24:"0x71,0",  25:"0x71,0",  26:"0x71,0",  27:"0x71,0",  28:"0x71,0",  29:"0x71,0",  30:"0x71,0",  31:"0x71,0",
 32:"0x71,1",  33:"0x71,1",  34:"0x71,1",  35:"0x71,1",  36:"0x71,1",  37:"0x71,1",  38:"0x71,1",  39:"0x71,1",
 40:"0x71,2",  41:"0x71,2",  42:"0x71,2",  43:"0x71,2",  44:"0x71,2",  45:"0x71,2",  46:"0x71,2",  47:"0x71,2",
 48:"0x71,3",  49:"0x71,3",  50:"0x71,3",  51:"0x71,3",  52:"0x71,3",  53:"0x71,3",  54:"0x71,3",  55:"0x71,3",
 56:"0x74,4",  57:"0x74,5" }

profile_48x25G_8x100G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,5",   5:"0x70,5",   6:"0x70,5",   7:"0x70,5",
  8:"0x70,6",   9:"0x70,6",  10:"0x70,6",  11:"0x70,6",  12:"0x70,7",  13:"0x70,7",  14:"0x70,7",  15:"0x70,7",
 16:"0x70,0",  17:"0x70,0",  18:"0x70,0",  19:"0x70,0",  20:"0x70,1",  21:"0x70,1",  22:"0x70,1",  23:"0x70,1",
 24:"0x70,2",  25:"0x70,2",  26:"0x70,2",  27:"0x70,2",  28:"0x70,3",  29:"0x70,3",  30:"0x70,3",  31:"0x70,3",
 32:"0x71,4",  33:"0x71,4",  34:"0x71,4",  35:"0x71,4",  36:"0x71,5",  37:"0x71,5",  38:"0x71,5",  39:"0x71,5",
 40:"0x71,6",  41:"0x71,6",  42:"0x71,6",  43:"0x71,6",  44:"0x71,7",  45:"0x71,7",  46:"0x71,7",  47:"0x71,7",
 48:"0x71,0",  49:"0x71,0",  50:"0x71,0",  51:"0x71,0",  52:"0x71,0",  53:"0x71,0",  54:"0x71,0",  55:"0x71,0",
 56:"0x71,1",  57:"0x71,1",  58:"0x71,1",  59:"0x71,1",  60:"0x71,1",  61:"0x71,1",  62:"0x71,1",  63:"0x71,1",
 64:"0x71,2",  65:"0x71,2",  66:"0x71,2",  67:"0x71,2",  68:"0x71,2",  69:"0x71,2",  70:"0x71,2",  71:"0x71,2",
 72:"0x71,3",  73:"0x71,3",  74:"0x71,3",  75:"0x71,3",  76:"0x71,3",  77:"0x71,3",  78:"0x71,3",  79:"0x71,3",
 80:"0x74,4",  81:"0x74,5" }

sfputil_profiles = {
 "FALCON16X25G":profile_16x25G,
 "FC16x25GIXIA":profile_16x25G_ixia,
 "FALCON16x400G":profile_16x400G,
 "FALCON128x50G":profile_16x400G,
 "FALCON64x100G":profile_16x400G,
 "FC16x100G8x400G":profile_16x400G,
 "FC24x100G4x400G":profile_16x400G,
 "FC32x100G8x400G":profile_16x400G,
 "FALCON64x25G":profile_64x25G,
 "FALCON32x25G64":profile_32x25G,
 "FC24x254x200G64":profile_24x25G_4x200G,
 "FC24x258x100G64":profile_24x25G_8x200G,
 "FC48x10G8x100G":profile_48x25G_8x100G,
 "FC48x25G8x100G":profile_48x25G_8x100G
}



# system level event/error
EVENT_ON_ALL_SFP = '-1'
SYSTEM_NOT_READY = 'system_not_ready'
SYSTEM_READY = 'system_become_ready'
SYSTEM_FAIL = 'system_fail'

PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
HOST_CHK_CMD = "docker > /dev/null 2>&1"
PLATFORM = "arm64-marvell_db98cx8540_16cd-r0"
HWSKU = "db98cx8540_16cd"

# SFP PORT numbers
SFP_PORT_START = 1
SFP_PORT_END = 132


SYSLOG_IDENTIFIER = "sfp_event"
sonic_logger = logger.Logger(SYSLOG_IDENTIFIER)

class sfp_event:
    ''' Listen to plugin/plugout cable events '''


    def __init__(self):
        
        self.handle = None
        self.port_to_eeprom_mapping = {}
        self.SFP_PORT_START=SFP_PORT_START
        self.SFP_PORT_END=SFP_PORT_END
        self.PLATFORM_ROOT_PATH=PLATFORM_ROOT_PATH
        self.PLATFORM=PLATFORM
        self.PMON_HWSKU_PATH=PMON_HWSKU_PATH
        self.HOST_CHK_CMD = HOST_CHK_CMD
        self.HWSKU = HWSKU

        eeprom_path="/sys/bus/i2c/devices/0-0050/eeprom"

        x = self.SFP_PORT_START
        while(x<self.SFP_PORT_END+1):
            self.port_to_eeprom_mapping[x] = eeprom_path
            x = x + 1
        path=self.__get_path_to_sai_file()
        cmd = "cat " + path + " | grep hwId | cut -f2 -d="
        port_profile = os.popen(cmd).read()
        self._port_profile = port_profile.split("\n")[0]
 
    def initialize(self):       
        self.modprs_register = 0 
        # Get Transceiver status
        time.sleep(5)
        self.modprs_register = self._get_transceiver_status()

    def deinitialize(self):
        if self.handle is None:
            return

    def __is_host(self):
        return os.system(self.HOST_CHK_CMD) == 0

    def i2c_set(self, device_addr, offset, value):
        if smbus_present == 0:
            cmd = "i2cset -y 0 " + hex(device_addr) + " " + hex(offset) + " " + hex(value)
            os.system(cmd)
        else:
            bus = smbus.SMBus(0)
            bus.write_byte_data(device_addr, offset, value)
      

    def _get_transceiver_status(self):
        if smbus_present == 0:
            sonic_logger.log_info("  PMON - smbus ERROR - DEBUG sfp_event   ")
        sfp_status = 0
        x = 0
        for index in range(self.SFP_PORT_START, self.SFP_PORT_END+1):
                port_index = index-1
                profile = sfputil_profiles[self._port_profile]
                if  port_index in profile:
                        offset = int(profile[port_index].split(",")[1])
                        bin_offset = 1<<offset
                        device_reg = int(profile[port_index].split(",")[0],16)
                        self.i2c_set(device_reg, 0, bin_offset)
                        path = "/sys/bus/i2c/devices/0-0050/eeprom"
                        try:
                                reg_file = open(path, 'rb')
                                reg_file.seek(1)
                                reg_file.read(2)
                                sfp_status=( x | (1<<index-self.SFP_PORT_START)) + sfp_status
                        except IOError as e:
                                sfp_status=( x & ~(1<<index-self.SFP_PORT_START)) + sfp_status

        sfp_status = ~sfp_status
        return sfp_status

    def __get_path_to_sai_file(self):
        platform_path = "/".join([self.PLATFORM_ROOT_PATH, self.PLATFORM])
        hwsku_path = "/".join([platform_path, self.HWSKU]
                              ) if self.__is_host() else self.PMON_HWSKU_PATH
        return "/".join([hwsku_path, "sai.profile"])

    def check_sfp_status(self, port_change, timeout):
        """
         check_sfp_status called from get_change_event,
            this will return correct status of all 4 SFP ports if there is a change in any of them 
        """
    
        start_time = time.time()
        port = self.SFP_PORT_START
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000) # Convert to secs
        else:
            return False, {}
        end_time = start_time + timeout

        if (start_time > end_time):
            return False, {} # Time wrap or possibly incorrect timeout

        while (timeout >= 0):
            # Check for OIR events and return updated port_change
            reg_value = self._get_transceiver_status()
            if (reg_value != self.modprs_register):
                changed_ports = (self.modprs_register ^ reg_value)
                while (port >= self.SFP_PORT_START and port <=self.SFP_PORT_END):
                    profile = sfputil_profiles[self._port_profile]
                    port_index = port - 1 
                    if  port_index in profile:
                        # Mask off the bit corresponding to our port
                        mask = (1 << port-SFP_PORT_START)
                        if (changed_ports & mask):
                                # ModPrsL is active high
                                if reg_value & mask == 0:
                                     port_change[port] = '1'
                                else:
                                     port_change[port] = '0'
                    port += 1
                # Update reg value
                self.modprs_register = reg_value
                return True, port_change

            if forever:
                time.sleep(1)
            else:
                timeout = end_time - time.time()
                if timeout >= 1:
                    time.sleep(1) # We poll at 1 second granularity
                else:
                    if timeout > 0:
                        time.sleep(timeout)
                    return True, {}
