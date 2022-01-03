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
    from sonic_py_common import logger
    from sonic_platform.component import Component

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

smbus_present = 1
try:
    import smbus
except ImportError as e:
    smbus_present = 0

MAX_COMPONENT=2
MAX_SELECT_DELAY = 3600
SFP_PORT_START = 1
SFP_PORT_END = 48
QSFP_PORT_START=49
QSFP_PORT_END=80
PORT_END = 80

# profile  port_num:<port_select_val, device_register, port_status_bit>
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
 48:"48,0x17,0",  49:"49,0x17,1",  50:"49,0x17,2",  51:"51,0x17,3",  52:"52,0x17,4",  53:"53,0x17,5",  54:"54,0x17,6",  55:"55,0x17,7",
}

sfputil_profiles = {
"F2T80x25G":profile_2T80x25G,
"F2T48x25G8x100G":profile_2T48x10G_8x100G,
"F2T48x10G8x100G":profile_2T48x10G_8x100G
}
SYSLOG_IDENTIFIER = "chassis"
sonic_logger=logger.Logger(SYSLOG_IDENTIFIER)
class Chassis(ChassisBase):
    """
    Platform-specific Chassis class
    derived from Dell S6000 platform.
    customized for db98cx8514_10cc platform.
    """
    reset_reason_dict = {}
    reset_reason_dict[0x02] = ChassisBase.REBOOT_CAUSE_POWER_LOSS
    reset_reason_dict[0x20] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC

    reset_reason_dict[0x08] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_CPU
    reset_reason_dict[0x10] = ChassisBase.REBOOT_CAUSE_WATCHDOG
    HWSKU = "db98cx8514_10cc"

    def __init__(self):
        ChassisBase.__init__(self)
        timeout=0
        # Port numbers for SFP List Initialization
        self.SFP_PORT_START = SFP_PORT_START
        self.SFP_PORT_END = SFP_PORT_END
        self.QSFP_PORT_START = QSFP_PORT_START
        self.QSFP_PORT_END = QSFP_PORT_END
        self.PORT_END = PORT_END

        sai_profile_path=self.__get_path_to_sai_profile_file()
        cmd = "cat " + sai_profile_path + " | grep hwId | cut -f2 -d="
        port_profile = os.popen(cmd).read()
        self._port_profile = port_profile.split("\n")[0]

        #Adding SFP port to sfp list
        for index in range(self.SFP_PORT_START, self.SFP_PORT_END+1):
            i2cdev = 2
            port=index-1
            profile = sfputil_profiles[self._port_profile]
            if port in profile:
                eeprom_path = '/sys/bus/i2c/devices/2-0050/eeprom'
                if not os.path.exists(eeprom_path):
                       sonic_logger.log_info(" DEBUG - path %s -- did not exist " % eeprom_path )
                sfp_node = Sfp(index, 'SFP', eeprom_path, i2cdev )
                self._sfp_list.append(sfp_node)
        #Adding QSFP port to sfp list
        for index in range(self.QSFP_PORT_START, self.QSFP_PORT_END+1):
            i2cdev = 2
            port=index-1
            profile = sfputil_profiles[self._port_profile]
            if port in profile:
                sfp_node = Sfp(index, 'QSFP', eeprom_path, i2cdev )
                self._sfp_list.append(sfp_node)

        self.sfp_event_initialized = False
        self._eeprom = Eeprom()
        for i in range(MAX_COMPONENT):
            component = Component(i)
            self._component_list.append(component)

    def __get_path_to_sai_profile_file(self):
        """
        Retrieve sai.profile path
        Returns:
            get_path_to_platform_dir(): get platform path depend on, whether we're running on container or on the host
            Returns sai.proile path.
        """
        from sonic_py_common import device_info
        platform_path = device_info.get_path_to_platform_dir()
        hwsku_path = "/".join([platform_path, self.HWSKU])
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

    def get_watchdog(self):
        """
        Retrieves hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device
        """
        try:
            if self._watchdog is None:
                from sonic_platform.watchdog import WatchdogImplBase
                watchdog_device_path = "/dev/watchdog0"
                self._watchdog = WatchdogImplBase(watchdog_device_path)
        except Exception as e:
            sonic_logger.log_warning(" Fail to load watchdog {}".format(repr(e)))

        return self._watchdog


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
            timeout = MAX_SELECT_DELAY
            while True:
                status = self.sfp_event.check_sfp_status( port_dict, timeout)
                if not port_dict == {}:
                    break
        else:
            # At boot up and in "INIT" state call from xrcvd will have a timeout value
            # return true without change after timeout and will transition to "SYSTEM_READY"
            status = self.sfp_event.check_sfp_status( port_dict, timeout)

        if status:
            return True, {'sfp':port_dict}
        else:
            return True, {'sfp':{}}

