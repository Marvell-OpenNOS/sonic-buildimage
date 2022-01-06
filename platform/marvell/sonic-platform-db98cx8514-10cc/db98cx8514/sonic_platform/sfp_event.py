#####################################################################
#listen to the SDK for the SFP change event and return to chassis.
#####################################################################

from __future__ import print_function
import os
import time
import sys
from sonic_py_common import logger

smbus_present = 1

try:
    import smbus
except ImportError as e:
    smbus_present = 0


if sys.version_info[0] < 3:
    import commands as command
else:
    import subprocess as command

# Port  Num:<port_select_bit,device_register,port_status_bit>
profile_2T80x25G = {
  0:"0,0x11,0",   1:"1,0x11,1",    2:"2,0x11,2",    3:"3,0x11,3",    4:"4,0x11,4",    5:"5,0x11,5",    6:"6,0x11,6",    7:"7,0x11,7",
  8:"8,0x12,0",   9:"9,0x12,1",    10:"10,0x12,2",  11:"11,0x12,3",  12:"12,0x12,4",  13:"13,0x12,5",  14:"14,0x12,6",  15:"15,0x12,7",
 16:"16,0x13,0",  17:"17,0x13,1",  18:"18,0x13,2",  19:"19,0x13,3",  20:"20,0x13,4",  21:"21,0x13,5",  22:"22,0x13,6",  23:"23,0x13,7",
 24:"24,0x14,0",  25:"25,0x14,1",  26:"26,0x14,2",  27:"27,0x14,3",  28:"28,0x14,4",  29:"29,0x14,5",  30:"30,0x14,6",  31:"31,0x14,7",
 32:"32,0x15,0",  33:"33,0x15,1",  34:"34,0x15,2",  35:"35,0x15,3",  36:"36,0x15,4",  37:"37,0x15,5",  38:"38,0x15,6",  39:"39,0x15,7",
 40:"40,0x16,0",  41:"41,0x16,1",  42:"42,0x16,2",  43:"43,0x16,3",  44:"44,0x16,4",  45:"45,0x16,5",  46:"46,0x16,6",  47:"47,0x16,7",
 48:"48,0x17,0",  49:"48,0x17,0",  50:"48,0x17,0",  51:"48,0x17,0",  52:"49,0x17,1",  53:"49,0x17,1",  54:"49,0x17,1",  55:"49,0x17,1",
 56:"50,0x17,2",  57:"50,0x17,2",  58:"50,0x17,2",  59:"50,0x17,2",  60:"51,0x17,3",  61:"51,0x17,3",  62:"51,0x17,3",  63:"51,0x17,3",
 64:"52,0x17,4",  65:"52,0x17,4",  66:"52,0x17,4",  67:"52,0x17,4",  68:"53,0x17,5",  69:"53,0x17,5",  70:"53,0x17,5",  71:"53,0x17,5",
 72:"54,0x17,6",  73:"54,0x17,6",  74:"54,0x17,6",  75:"54,0x17,6",  76:"55,0x17,7",  77:"55,0x17,7",  78:"55,0x17,7",  79:"55,0x17,7",
}

profile_2T48x10G_8x100G = {
  0:"0,0x11,0",   1:"1,0x11,1",    2:"2,0x11,2",    3:"3,0x11,3",    4:"4,0x11,4",    5:"5,0x11,5",    6:"6,0x11,6",    7:"7,0x11,7",
  8:"8,0x12,0",   9:"9,0x12,1",    10:"10,0x12,2",  11:"11,0x12,3",  12:"12,0x12,4",  13:"13,0x12,5",  14:"14,0x12,6",  15:"15,0x12,7",
 16:"16,0x13,0",  17:"17,0x13,1",  18:"18,0x13,2",  19:"19,0x13,3",  20:"20,0x13,4",  21:"21,0x13,5",  22:"22,0x13,6",  23:"23,0x13,7",
 24:"24,0x14,0",  25:"25,0x14,1",  26:"26,0x14,2",  27:"27,0x14,3",  28:"28,0x14,4",  29:"29,0x14,5",  30:"30,0x14,6",  31:"31,0x14,7",
 32:"32,0x15,0",  33:"33,0x15,1",  34:"34,0x15,2",  35:"35,0x15,3",  36:"36,0x15,4",  37:"37,0x15,5",  38:"38,0x15,6",  39:"39,0x15,7",
 40:"40,0x16,0",  41:"41,0x16,1",  42:"42,0x16,2",  43:"43,0x16,3",  44:"44,0x16,4",  45:"45,0x16,5",  46:"46,0x16,6",  47:"47,0x16,7",
 48:"48,0x17,0",  49:"49,0x17,1",  50:"50,0x17,2",  51:"51,0x17,3",  52:"52,0x17,4",  53:"53,0x17,5",  54:"54,0x17,6",  55:"55,0x17,7",
}

sfputil_profiles = {
"F2T80x25G":profile_2T80x25G,
"F2T48x25G8x100G":profile_2T48x10G_8x100G,
"F2T48x10G8x100G":profile_2T48x10G_8x100G
}


# system level event/error
EVENT_ON_ALL_SFP = '-1'
SYSTEM_NOT_READY = 'system_not_ready'
SYSTEM_READY = 'system_become_ready'
SYSTEM_FAIL = 'system_fail'
#PORT numbers
PORT_START = 1
PORT_END = 80
SYSLOG_IDENTIFIER = "sfp_event"
sonic_logger = logger.Logger(SYSLOG_IDENTIFIER)

class sfp_event:
    ''' Listen to plugin/plugout cable events '''

    HWSKU = "db98cx8514_10cc"
    def __init__(self):
        
        self.handle = None
        self.port_to_eeprom_mapping = {}
        self.PORT_START=PORT_START
        self.PORT_END=PORT_END
        eeprom_path="/sys/bus/i2c/devices/2-0050/eeprom"

        x = self.PORT_START
        while(x<self.PORT_END+1):
            self.port_to_eeprom_mapping[x] = eeprom_path
            x = x + 1
        #Reading currenr port profile
        path=self.__get_path_to_sai_file()
        cmd = "cat " + path + " | grep hwId | cut -f2 -d="
        port_profile = os.popen(cmd).read()
        self._port_profile = port_profile.split("\n")[0]
 
    def initialize(self):       
        self.modprs_register = 0 
        # Get Transceiver status
        time.sleep(5)
        self.modprs_register = self.get_transceiver_status()

    def deinitialize(self):
        if self.handle is None:
            return

    def i2c_set(self, device_addr, offset, value):
        if smbus_present == 0:
            cmd = "i2cset -y 2 " + hex(device_addr) + " " + hex(offset) + " " + hex(value)
            os.system(cmd)
        else:
            bus = smbus.SMBus(2)
            bus.write_byte_data(device_addr, offset, value)
      

    def get_transceiver_status(self):
        if smbus_present == 0:
            sfpstatus_bin = ''
            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x11') 
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x12')
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x13') 
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x14')
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x15')
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x16')
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin
            
            cmdstatus, sfpstatus = cmd.getstatusoutput('i2cget -y 2 0x30 0x17')
            sfpstatus = int(sfpstatus, 16)
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            sfpstatus_bin = ''.join('1' if j == '0' else '0' for j in sfpstatus_bin)
            sfpstatus = int(sfpstatus_bin,2)
        else:
            sfpstatus_bin = ''
            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x11
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x12
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin =  (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin


            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x13
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin =  (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x14
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin =  (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x15
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x16
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin
            
            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x30
            DEVICE_REG = 0x17
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)  
            sfpstatus_bin = (format(sfpstatus, '#010b')).split('0b')[1] + sfpstatus_bin

            #logger.log_info("Current SFP presence in bin   =   %s" % sfpstatus_bin )
            sfpstatus_bin = ''.join('1' if j == '0' else '0' for j in sfpstatus_bin)
            sfpstatus = int(sfpstatus_bin, 2)

        return sfpstatus
    def __get_path_to_sai_file(self):
        """
        Retrieve sai.profile path
        Returns:
             get_path_to_platform_dir() : get platform path depend on, whether we're running on container or on the host.
             Returns sai.proile path.
        """
        from sonic_py_common import device_info
        platform_path = device_info.get_path_to_platform_dir()
        hwsku_path = "/".join([platform_path, self.HWSKU])
        return "/".join([hwsku_path, "sai.profile"])

    def check_sfp_status(self, port_change, timeout):
        """
         check_sfp_status called from get_change_event,
         this will return correct status of all ports if there is a change in any of them 
        """
    
        start_time = time.time()
        port = self.PORT_START
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
            all_port_status = self.get_transceiver_status()

            if (all_port_status != self.modprs_register):
                changed_ports = (self.modprs_register ^ all_port_status)

                while (port >= self.PORT_START and port <=self.PORT_END):
                    profile = sfputil_profiles[self._port_profile]
                    port_index = port - 1
                    if  port_index in profile:
                        #Mask off the bit corresponding to our port
                        real_port= int(profile[port_index].split(",")[0])
                        mask = (1 << real_port)
                        y=(changed_ports & mask)
                        if (changed_ports & mask):
                                if all_port_status & mask == 0:
                                     port_change[port] = '0'
                                else:
                                     port_change[port] = '1'
                    port += 1
                # Update reg value
                self.modprs_register = all_port_status
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
            
        return False, {}
