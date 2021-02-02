#!/usr/bin/env python

########################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs' information which are available in the platform
#
########################################################################


try:
    import sys
    from sonic_platform_base.psu_base import PsuBase
    from sonic_daemon_base.daemon_base import Logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

if sys.version_info[0] < 3:
    import commands as cmd
else:
    import subprocess as cmd

smbus_present = 1
try:
   import smbus
except ImportError as e:
   smbus_present = 0 

logger = Logger('psu')

   
class Psu(PsuBase):

    def __init__(self, psu_index):
        self.index = psu_index + 1
        self._fan_list = []


    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "PSU{}".format(self.index)

    def get_presence(self):
        """
        Retrieves the presence of the Power Supply Unit (PSU)

        Returns:
            bool: True if PSU is present, False if not
        """

        if smbus_present == 0: # if called from psuutil outside of pmon
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 2 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
             
        if self.index == 1:
             psustatus = psustatus&1
             if psustatus == 1 :
                 return False
        if self.index == 2:
            psustatus = psustatus&2
            if psustatus == 2 :
                return False
  
        return True

    def get_model(self):
        """
        Retrieves the part number of the PSU

        Returns:
            string: Part number of PSU
        """
        return self.eeprom.modelstr()

    def get_serial(self):
        """
        Retrieves the serial number of the PSU

        Returns:
            string: Serial number of PSU
        """
        return self.eeprom.serial_number_str()

    def get_status(self):
        """
        Retrieves the operational status of the PSU

        Returns:
            bool: True if PSU is operating properly, False if not
        """

        if smbus_present == 0: 
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 2 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus&4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
                return True
                    
        return False


    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        return  

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, electric current in amperes,
            e.g. 15.4
        """
        psu_current = 0.0
        return psu_current

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts,
            e.g. 302.6
        """
       
        psu_power = 0.0
        return psu_power

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and
            passed all its internal self-tests, False if not.
        """

        if smbus_present == 0: 
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 2 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus&4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
                return True
                    
        return False
        

    def get_status_led(self):
        """
        Gets the state of the PSU status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
	return
    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the
                   PSU status LED
        Returns:
            bool: True if status LED state is set successfully, False if
                  not
        """
        return 
