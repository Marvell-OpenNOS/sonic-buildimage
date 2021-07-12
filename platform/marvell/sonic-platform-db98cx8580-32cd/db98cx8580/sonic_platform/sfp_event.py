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


profile_32x400G = {
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
128:"0x72,4", 129:"0x72,4", 130:"0x72,4", 131:"0x72,4", 132:"0x72,4", 133:"0x72,4", 134:"0x72,4", 135:"0x72,4",
136:"0x72,5", 137:"0x72,5", 138:"0x72,5", 139:"0x72,5", 140:"0x72,5", 141:"0x72,5", 142:"0x72,5", 143:"0x72,5",
144:"0x72,6", 145:"0x72,6", 146:"0x72,6", 147:"0x72,6", 148:"0x72,6", 149:"0x72,6", 150:"0x72,6", 151:"0x72,6",
152:"0x72,7", 153:"0x72,7", 154:"0x72,7", 155:"0x72,7", 156:"0x72,7", 157:"0x72,7", 158:"0x72,7", 159:"0x72,7",
160:"0x72,0", 161:"0x72,0", 162:"0x72,0", 163:"0x72,0", 164:"0x72,0", 165:"0x72,0", 166:"0x72,0", 167:"0x72,0",
168:"0x72,1", 169:"0x72,1", 170:"0x72,1", 171:"0x72,1", 172:"0x72,1", 173:"0x72,1", 174:"0x72,1", 175:"0x72,1",
176:"0x72,2", 177:"0x72,2", 178:"0x72,2", 179:"0x72,2", 180:"0x72,2", 181:"0x72,2", 182:"0x72,2", 183:"0x72,2",
184:"0x72,3", 185:"0x72,3", 186:"0x72,3", 187:"0x72,3", 188:"0x72,3", 189:"0x72,3", 190:"0x72,3", 191:"0x72,3",
192:"0x73,4", 193:"0x73,4", 194:"0x73,4", 195:"0x73,4", 196:"0x73,4", 197:"0x73,4", 198:"0x73,4", 199:"0x73,4",
200:"0x73,5", 201:"0x73,5", 202:"0x73,5", 203:"0x73,5", 204:"0x73,5", 205:"0x73,5", 206:"0x73,5", 207:"0x73,5",
208:"0x73,6", 209:"0x73,6", 210:"0x73,6", 211:"0x73,6", 212:"0x73,6", 213:"0x73,6", 214:"0x73,6", 215:"0x73,6",
216:"0x73,7", 217:"0x73,7", 218:"0x73,7", 219:"0x73,7", 220:"0x73,7", 221:"0x73,7", 222:"0x73,7", 223:"0x73,7",
224:"0x73,0", 225:"0x73,0", 226:"0x73,0", 227:"0x73,0", 228:"0x73,0", 229:"0x73,0", 230:"0x73,0", 231:"0x73,0",
232:"0x73,1", 233:"0x73,1", 234:"0x73,1", 235:"0x73,1", 236:"0x73,1", 237:"0x73,1", 238:"0x73,1", 239:"0x73,1",
240:"0x73,2", 241:"0x73,2", 242:"0x73,2", 243:"0x73,2", 244:"0x73,2", 245:"0x73,2", 246:"0x73,2", 247:"0x73,2",
248:"0x73,3", 249:"0x73,3", 250:"0x73,3", 251:"0x73,3", 252:"0x73,3", 253:"0x73,3", 254:"0x73,3", 255:"0x73,3",
256:"0x74,4" }


profile_128x10G = {
  0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,5",   5:"0x70,5",   6:"0x70,5",   7:"0x70,5",
  8:"0x70,6",   9:"0x70,6",  10:"0x70,6",  11:"0x70,6",  12:"0x70,7",  13:"0x70,7",  14:"0x70,7",  15:"0x70,7",
 16:"0x70,0",  17:"0x70,0",  18:"0x70,0",  19:"0x70,0",  20:"0x70,1",  21:"0x70,1",  22:"0x70,1",  23:"0x70,1",
 24:"0x70,2",  25:"0x70,2",  26:"0x70,2",  27:"0x70,2",  28:"0x70,3",  29:"0x70,3",  30:"0x70,3",  31:"0x70,3",
 32:"0x71,4",  33:"0x71,4",  34:"0x71,4",  35:"0x71,4",  36:"0x71,5",  37:"0x71,5",  38:"0x71,5",  39:"0x71,5",
 40:"0x71,6",  41:"0x71,6",  42:"0x71,6",  43:"0x71,6",  44:"0x71,7",  45:"0x71,7",  46:"0x71,7",  47:"0x71,7",
 48:"0x71,0",  49:"0x71,0",  50:"0x71,0",  51:"0x71,0",  52:"0x71,1",  53:"0x71,1",  54:"0x71,1",  55:"0x71,1",
 56:"0x71,2",  57:"0x71,2",  58:"0x71,2",  59:"0x71,2",  60:"0x71,3",  61:"0x71,3",  62:"0x71,3",  63:"0x71,3",
 64:"0x72,4",  65:"0x72,4",  66:"0x72,4",  67:"0x72,4",  68:"0x72,5",  69:"0x72,5",  70:"0x72,5",  71:"0x72,5",
 72:"0x72,6",  73:"0x72,6",  74:"0x72,6",  75:"0x72,6",  76:"0x72,7",  77:"0x72,7",  78:"0x72,7",  79:"0x72,7",
 80:"0x72,0",  81:"0x72,0",  82:"0x72,0",  83:"0x72,0",  84:"0x72,1",  85:"0x72,1",  86:"0x72,1",  87:"0x72,1",
 88:"0x72,2",  89:"0x72,2",  90:"0x72,2",  91:"0x72,2",  92:"0x72,3",  93:"0x72,3",  94:"0x72,3",  95:"0x72,3",
 96:"0x73,4",  97:"0x73,4",  98:"0x73,4",  99:"0x73,4", 100:"0x73,5", 101:"0x73,5", 102:"0x73,5", 103:"0x73,5",
104:"0x73,6", 105:"0x73,6", 106:"0x73,6", 107:"0x73,6", 108:"0x73,7", 109:"0x73,7", 110:"0x73,7", 111:"0x73,7",
112:"0x73,0", 113:"0x73,0", 114:"0x73,0", 115:"0x73,0", 116:"0x73,1", 117:"0x73,1", 118:"0x73,1", 119:"0x73,1",
120:"0x73,2", 121:"0x73,2", 122:"0x73,2", 123:"0x73,2", 124:"0x73,3", 125:"0x73,3", 126:"0x73,3", 127:"0x73,3",
128:"0x74,4" }

profile_32x25G = {
 0:"0x70,4",   1:"0x70,5",   2:"0x70,6",   3:"0x70,7",   4:"0x70,0",   5:"0x70,1",   6:"0x70,2",   7:"0x70,3",
 8:"0x71,4",   9:"0x71,5",  10:"0x71,6",  11:"0x71,7",  12:"0x71,0",  13:"0x71,1",  14:"0x71,2",  15:"0x71,3",
16:"0x72,4",  17:"0x72,5",  18:"0x72,6",  19:"0x72,7",  20:"0x72,0",  21:"0x72,1",  22:"0x72,2",  23:"0x72,3",
24:"0x73,4",  25:"0x73,5",  26:"0x73,6",  27:"0x73,7",  28:"0x73,0",  29:"0x73,1",  30:"0x73,2",  31:"0x73,3",
32:"0x74,4" }

profile_32x25G_ixia = {
 0:"0x70,4",   1:"0x70,4",   2:"0x70,4",   3:"0x70,4",   4:"0x70,5",   5:"0x70,5",   6:"0x70,5",   7:"0x70,5",
 8:"0x70,6",   9:"0x70,6",  10:"0x70,6",  11:"0x70,6",  12:"0x70,7",  13:"0x70,7",  14:"0x70,7",  15:"0x70,7",
16:"0x70,0",  17:"0x70,0",  18:"0x70,0",  19:"0x70,0",  20:"0x70,1",  21:"0x70,1",  22:"0x70,1",  23:"0x70,1",
24:"0x70,2",  25:"0x70,2",  26:"0x70,2",  27:"0x70,2",  28:"0x70,3",  29:"0x70,3",  30:"0x70,3",  31:"0x70,3",
32:"0x74,4" }

profile_24x25G_8x200G = {
 0:"0x70,4",   1:"0x70,5",   2:"0x70,6",   3:"0x70,7",   4:"0x70,0",   5:"0x70,1",   6:"0x70,2",   7:"0x70,3",
 8:"0x71,4",   9:"0x71,5",  10:"0x71,6",  11:"0x71,7",  12:"0x71,0",  13:"0x71,1",  14:"0x71,2",  15:"0x71,3",
16:"0x72,4",  17:"0x72,5",  18:"0x72,6",  19:"0x72,7",  20:"0x72,0",  21:"0x72,1",  22:"0x72,2",  23:"0x72,3",
24:"0x73,4",  25:"0x73,4",  26:"0x73,4",  27:"0x73,4",  28:"0x73,5",  29:"0x73,5",  30:"0x73,5",  31:"0x73,5",
32:"0x73,6",  33:"0x73,6",  34:"0x73,6",  35:"0x73,6",  36:"0x73,7",  37:"0x73,7",  38:"0x73,7",  39:"0x73,7",
40:"0x73,0",  41:"0x73,0",  42:"0x73,0",  43:"0x73,0",  44:"0x73,1",  45:"0x73,1",  46:"0x73,1",  47:"0x73,1",
48:"0x73,2",  49:"0x73,2",  50:"0x73,2",  51:"0x73,2",  52:"0x73,3",  53:"0x73,3",  54:"0x73,3",  55:"0x73,3",
56:"0x74,4" }

profile_24x25G_4x200G = {
 0:"0x70,4",   1:"0x70,5",   2:"0x70,6",   3:"0x70,7",   4:"0x70,0",   5:"0x70,1",   6:"0x70,2",   7:"0x70,3",
 8:"0x71,4",   9:"0x71,5",  10:"0x71,6",  11:"0x71,7",  12:"0x71,0",  13:"0x71,1",  14:"0x71,2",  15:"0x71,3",
16:"0x72,4",  17:"0x72,5",  18:"0x72,6",  19:"0x72,7",  20:"0x72,0",  21:"0x72,1",  22:"0x72,2",  23:"0x72,3",
24:"0x73,4",  25:"0x73,4",  26:"0x73,4",  27:"0x73,4",  28:"0x73,5",  29:"0x73,5",  30:"0x73,5",  31:"0x73,5",
32:"0x73,6",  33:"0x73,6",  34:"0x73,6",  35:"0x73,6",  36:"0x73,7",  37:"0x73,7",  38:"0x73,7",  39:"0x73,7",
40:"0x74,4" }

sfputil_profiles = {
 "FALCON32X25G":profile_32x25G,
 "FC32x25GIXIA":profile_32x25G_ixia,
 "FALCON32x400G":profile_32x400G,
 "FALCON128x100G":profile_32x400G,
 "FALCON64x100GR4":profile_32x400G,
 "FC32x10016x400G":profile_32x400G,
 "FC48x100G8x400G":profile_32x400G,
 "FC96x100G8x400G":profile_32x400G,
 "FALCON128x10G":profile_128x10G,
 "FALCON128x25G":profile_128x10G,
 "FC64x25G64x10G":profile_128x10G,
 "FC24x25G4x200G":profile_24x25G_4x200G,
 "FC24x25G8x200G":profile_24x25G_8x200G,
 "FALCONEBOF":profile_24x25G_8x200G
}



# system level event/error
EVENT_ON_ALL_SFP = '-1'
SYSTEM_NOT_READY = 'system_not_ready'
SYSTEM_READY = 'system_become_ready'
SYSTEM_FAIL = 'system_fail'

PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
HOST_CHK_CMD = "docker > /dev/null 2>&1"
PLATFORM = "x86_64-marvell_db98cx8580_32cd-r0"
HWSKU = "db98cx8580_32cd"

# SFP PORT numbers
SFP_PORT_START = 1
SFP_PORT_END = 257


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

        eeprom_path="/sys/bus/i2c/devices/2-0050/eeprom"

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
            cmd = "i2cset -y 2 " + hex(device_addr) + " " + hex(offset) + " " + hex(value)
            os.system(cmd)
        else:
            bus = smbus.SMBus(2)
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
                        path = "/sys/bus/i2c/devices/2-0050/eeprom"
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
