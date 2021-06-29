#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################

try:
    import os
    import sys
    import glob
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import Sfp
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.fan import Fan
    from .fan_drawer import RealDrawer
    from sonic_platform.psu import Psu
    from sonic_platform.thermal import Thermal
    from sonic_platform.component import Component
    from sonic_py_common import logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

smbus_present = 1
try:
    import smbus
except ImportError as e:
    smbus_present = 0

MAX_SELECT_DELAY = 3600
COPPER_PORT_START = 1
COPPER_PORT_END = 48
SFP_PORT_START = 49
SFP_PORT_END = 52
PORT_END = 52

# Device counts
MAX_FAN_DRAWERS = 2
MAX_FANS_PER_DRAWER = 1
MAX_PSU = 2
MAX_THERMAL = 6

# Temp - disable these to help with early debug
MAX_COMPONENT = 2

SYSLOG_IDENTIFIER = "chassis"
sonic_logger = logger.Logger(SYSLOG_IDENTIFIER)


class Chassis(ChassisBase):
    """
        Platform-specific Chassis class
        Derived from Dell S6000 platform.
        customized for the et6448m platform.
    """

    def __init__(self):
        ChassisBase.__init__(self)
        self.system_led_supported_color = ['off', 'amber', 'green', 'amber_blink', 'green_blink']
        # Port numbers for SFP List Initialization
        self.COPPER_PORT_START = COPPER_PORT_START
        self.COPPER_PORT_END = COPPER_PORT_END
        self.SFP_PORT_START = SFP_PORT_START
        self.SFP_PORT_END = SFP_PORT_END
        self.PORT_END = PORT_END

        # for non-sfp ports create dummy objects for copper / non-sfp ports
        for index in range(self.COPPER_PORT_START, self.COPPER_PORT_END+1):
            sfp_node = Sfp(index, 'COPPER', 'N/A', 'N/A')
            self._sfp_list.append(sfp_node)

        # Verify optoe2 driver SFP eeprom devices were enumerated and exist
        # then create the sfp nodes
        eeprom_path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/eeprom"
        mux_dev = sorted(glob.glob("/sys/class/i2c-adapter/i2c-0/i2c-[0-9]"))
        y = 0
        for index in range(self.SFP_PORT_START, self.SFP_PORT_END+1):
            mux_dev_num = mux_dev[y]
            port_i2c_map = mux_dev_num[-1]
            y = y + 1
            port_eeprom_path = eeprom_path.format(port_i2c_map)
            if not os.path.exists(port_eeprom_path):
                sonic_logger.log_info("path %s didnt exist" % port_eeprom_path)
            sfp_node = Sfp(index, 'SFP', port_eeprom_path, port_i2c_map)
            self._sfp_list.append(sfp_node)
        self.sfp_event_initialized = False

        # Instantiate system eeprom object
        self._eeprom = Eeprom()

        # Construct lists fans, power supplies, thermals & components
        drawer_num = MAX_FAN_DRAWERS
        fan_num_per_drawer = MAX_FANS_PER_DRAWER
        drawer_ctor = RealDrawer
        fan_index = 0
        for drawer_index in range(drawer_num):
            drawer = drawer_ctor(drawer_index)
            self._fan_drawer_list.append(drawer)
            for index in range(fan_num_per_drawer):
                fan = Fan(fan_index, drawer)
                fan_index += 1
                drawer._fan_list.append(fan)
                self._fan_list.append(fan)

        for i in range(MAX_PSU):
            psu = Psu(i)
            self._psu_list.append(psu)

        for i in range(MAX_THERMAL):
            thermal = Thermal(i)
            self._thermal_list.append(thermal)

        for i in range(MAX_COMPONENT):
            component = Component(i)
            self._component_list.append(component)

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of physical SFP ports in a
            chassis starting from 1.

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

    def get_service_tag(self):
        """
        Retrieves the Service Tag of the chassis
        Returns:
            string: Service Tag of chassis
        """
        return self._eeprom.service_tag_str()

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

    def get_serial(self):
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
        # The et6448m CPLD does not have a hardware reboot cause register so
        # the hardware portion of reboot cause can't be implemented

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
                status = self.sfp_event.check_sfp_status(port_dict, timeout)
                if not port_dict == {}:
                    break
        else:
            # At boot up and in "INIT" state call from xrcvd will have timeout
            # value return true without change after timeout and will
            # transition to "SYSTEM_READY"
            status = self.sfp_event.check_sfp_status(port_dict, timeout)

        if status:
            return True, {'sfp': port_dict}
        else:
            return True, {'sfp': {}}

    def get_thermal_manager(self):
        from .thermal_manager import ThermalManager
        return ThermalManager

    def set_status_led(self, color):
        """
        Sets the state of the system LED

        Args:
            color: A string representing the color with which to set the
                   system LED

        Returns:
            bool: True if system LED state is set successfully, False if not
        """
        if color not in self.system_led_supported_color:
            return False

        if (color == 'off'):
            value = 0x00
        elif (color == 'amber'):
            value = 0x01
        elif (color == 'green'):
            value = 0x02
        elif (color == 'amber_blink'):
            value = 0x03
        elif (color == 'green_blink'):
            value = 0x04
        else:
            return False

        # Write sys led
        if smbus_present == 0:
            sonic_logger.log_warning("PMON LED SET -> smbus present = 0")
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICEREG = 0x7
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, value)
            sonic_logger.log_info("  System LED set O.K.  ")
            return True

        return False

    def get_status_led(self):
        """
        Gets the state of the system LED

        Returns:
            A string, one of the valid LED color strings which could be vendor
            specified.
        """
        # Read sys led
        if smbus_present == 0:
            sonic_logger.log_warning("PMON LED GET -> smbus present = 0")
            return False
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0x7
            value = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

            if value == 0x00:
                color = 'off'
            elif value == 0x01:
                color = 'amber'
            elif value == 0x02:
                color = 'green'
            elif value == 0x03:
                color = 'amber_blink'
            elif value == 0x04:
                color = 'green_blink'
            else:
                return False

            return color

    def get_watchdog(self):
        """
        Retrieves hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device

        Note:
            We overload this method to ensure that watchdog is only initialized
            when it is referenced. Currently, only one daemon can open the
            watchdog. To initialize watchdog in the constructor causes multiple
            daemon try opening watchdog when loading and constructing a chassis
            object and fail. By doing so we can eliminate that risk.
        """
        try:
            if self._watchdog is None:
                from sonic_platform.watchdog import WatchdogImplBase
                watchdog_device_path = "/dev/watchdog0"
                self._watchdog = WatchdogImplBase(watchdog_device_path)
        except Exception as e:
            sonic_logger.log_warning(" Fail to load watchdog {}".format(repr(e)))

        return self._watchdog

    def get_position_in_parent(self):
        """
		Retrieves 1-based relative physical position in parent device. If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of entPhysicalContainedIn is '0', then the value '-1' is returned
		Returns:
		    integer: The 1-based relative physical position in parent device or -1 if cannot determine the position
		"""
        return -1

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False
