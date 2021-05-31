#!/usr/bin/env python
##################################################################
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
##################################################################

try:
    import os
    import sys
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import Sfp
    from sonic_platform.eeprom import Eeprom
    from sonic_daemon_base.daemon_base import Logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

MAX_SELECT_DELAY = 3600
COPPER_PORT_START = 0
COPPER_PORT_END = 0
SFP_PORT_START = 1
SFP_PORT_END = 132
PORT_END = 132


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


SYSLOG_IDENTIFIER = "chassis"
logger = Logger()

class Chassis(ChassisBase):
    """
    Platform-specific Chassis class
    derived from Dell S6000 platform.
    customized for the platform.
    """
    reset_reason_dict = {}
    reset_reason_dict[0x02] = ChassisBase.REBOOT_CAUSE_POWER_LOSS
    reset_reason_dict[0x20] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC

    reset_reason_dict[0x08] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_CPU
    reset_reason_dict[0x10] = ChassisBase.REBOOT_CAUSE_WATCHDOG
    PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
    PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
    HOST_CHK_CMD = "docker > /dev/null 2>&1"
    PLATFORM = "arm64-marvell_db98cx8540_16cd-r0"
    HWSKU = "db98cx8540_16cd"


    def __init__(self):
        ChassisBase.__init__(self)
        # Port numbers for Initialize SFP list
        self.COPPER_PORT_START = COPPER_PORT_START
        self.COPPER_PORT_END = COPPER_PORT_END
        self.SFP_PORT_START = SFP_PORT_START
        self.SFP_PORT_END = SFP_PORT_END
        self.PORT_END = PORT_END

        sai_profile_path=self.__get_path_to_sai_profile_file()
        cmd = "cat " + sai_profile_path + " | grep hwId | cut -f2 -d="
        port_profile = os.popen(cmd).read()
        self._port_profile = port_profile.split("\n")[0]

	if not os.path.exists("/sys/bus/i2c/devices/0-0050") :
             os.system("echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-0/new_device")
        eeprom_path = '/sys/bus/i2c/devices/0-0050/eeprom'

        for index in range(self.SFP_PORT_START, self.SFP_PORT_END+1):
            i2cdev = 0
            port_eeprom_path = eeprom_path
            profile = sfputil_profiles[self._port_profile]
            if not os.path.exists(port_eeprom_path):
	    	logger.log_info(" DEBUG - path %s -- did not exist " % port_eeprom_path )
            if index in profile:
                sfp_node = Sfp(index, 'QSFP', port_eeprom_path, i2cdev )
                self._sfp_list.append(sfp_node)
        self.sfp_event_initialized = False

        # Instantiate ONIE system eeprom object
        self._eeprom = Eeprom()

    def __is_host(self):
        return os.system(self.HOST_CHK_CMD) == 0

    def __get_path_to_sai_profile_file(self):
        platform_path = "/".join([self.PLATFORM_ROOT_PATH, self.PLATFORM])
        hwsku_path = "/".join([platform_path, self.HWSKU]
                                ) if self.__is_host() else self.PMON_HWSKU_PATH
        return "/".join([hwsku_path, "sai.profile"])


    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of physical SFP ports in a chassis,
            starting from 1.
            For example, 1 for first SFP port in the chassis and so on.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None
        try:
            # The index will start from 1
            sfp = self._sfp_list[index-1]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (1-{})\n".format(
                             index, len(self._sfp_list)))
        return sfp

    def get_name(self):
        """
        Retrieves the name of the chassis
        Returns:
            string: The name of the chassis
        """
        return self._eeprom.modelstr()

    def get_presence(self):
        """
        Retrieves the presence of the chassis
        Returns:
            bool: True if chassis is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the chassis
        Returns:
            string: Model/part number of chassis
        """
        return self._eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the chassis (Service tag)
        Returns:
            string: Serial number of chassis
        """
        return self._eeprom.serial_str()

    def get_status(self):
        """
        Retrieves the operational status of the chassis
        Returns:
            bool: A boolean value, True if chassis is operating properly
            False if not
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.base_mac_addr()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this
            chassis.
        """
        return self._eeprom.serial_number_str()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the
        chassis

        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their
            corresponding values.
        """
        return self._eeprom.system_eeprom_info()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        #lrr = self._get_cpld_register('mb_reboot_cause')
        #if (lrr != 'ERR'):
        #    reset_reason = lrr
        #    if (reset_reason in self.reset_reason_dict):
        #        return (self.reset_reason_dict[reset_reason], None)
        #
        return (ChassisBase.REBOOT_CAUSE_NON_HARDWARE, None)

    def get_change_event(self, timeout=0):
        """
        Returns a nested dictionary containing all devices which have
        experienced a change at chassis level
        Args:
            timeout: Timeout in milliseconds (optional). If timeout == 0,
                this method will block until a change is detected.
        Returns:
            (bool, dict):
                - True if call successful, False if not;
                - A nested dictionary where key is a device type,
                  value is a dictionary with key:value pairs in the format of
                  {'device_id':'device_event'},
                  where device_id is the device ID for this device and
                        device_event,
                             status='1' represents device inserted,
                             status='0' represents device removed.
                  Ex. {'fan':{'0':'0', '2':'1'}, 'sfp':{'11':'0'}}
                      indicates that fan 0 has been removed, fan 2
                      has been inserted and sfp 11 has been removed.
        """
        # Initialize SFP event first
        if not self.sfp_event_initialized:
            from sonic_platform.sfp_event import sfp_event
            self.sfp_event = sfp_event()
            self.sfp_event.initialize()
            self.MAX_SELECT_EVENT_RETURNED = self.PORT_END
            self.sfp_event_initialized = True

        wait_for_ever = (timeout == 0)
        port_dict = {}
        if wait_for_ever:
            # xrcvd will call this monitor loop in the "SYSTEM_READY" state
            # logger.log_info(" wait_for_ever get_change_event %d" % timeout)
            timeout = MAX_SELECT_DELAY
            while True:
                status = self.sfp_event.check_sfp_status( port_dict, timeout)
                if not port_dict == {}:
                    break
        else:
            # At boot up and in "INIT" state call from xrcvd will have a timeout value
            # return true without change after timeout and will transition to "SYSTEM_READY"
            # logger.log_info(" initial get_change_event %d" % timeout )
            status = self.sfp_event.check_sfp_status( port_dict, timeout)

        if status:
            return True, {'sfp':port_dict}
        else:
            return True, {'sfp':{}}

