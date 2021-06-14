#!/usr/bin/env python

#############################################################################
# Mellanox
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform_base.component_base import ComponentBase
    from sonic_py_common import device_info
    from sonic_py_common.logger import Logger
    from os import listdir
    from os.path import isfile, join
    import sys
    import io
    import re
    import syslog
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

MAX_SELECT_DELAY = 3600

MLNX_NUM_PSU = 2

DMI_FILE = '/sys/firmware/dmi/entries/2-0/raw'
DMI_HEADER_LEN = 15
DMI_PRODUCT_NAME = "Product Name"
DMI_MANUFACTURER = "Manufacturer"
DMI_VERSION = "Version"
DMI_SERIAL = "Serial Number"
DMI_ASSET_TAG = "Asset Tag"
DMI_LOC = "Location In Chassis"
DMI_TABLE_MAP = {
                    DMI_PRODUCT_NAME: 0,
                    DMI_MANUFACTURER: 1,
                    DMI_VERSION: 2,
                    DMI_SERIAL: 3,
                    DMI_ASSET_TAG: 4,
                    DMI_LOC: 5
                }

EEPROM_CACHE_ROOT = '/var/cache/sonic/decode-syseeprom'
EEPROM_CACHE_FILE = 'syseeprom_cache'

HWMGMT_SYSTEM_ROOT = '/var/run/hw-management/system/'

MST_DEVICE_NAME_PATTERN = '/dev/mst/mt[0-9]*_pciconf0'
MST_DEVICE_RE_PATTERN = '/dev/mst/mt([0-9]*)_pciconf0'
SPECTRUM1_CHIP_ID = '52100'

#reboot cause related definitions
REBOOT_CAUSE_ROOT = HWMGMT_SYSTEM_ROOT

REBOOT_CAUSE_FILE_LENGTH = 1

# Global logger class instance
logger = Logger()

# magic code defnition for port number, qsfp port position of each Platform
# port_position_tuple = (PORT_START, QSFP_PORT_START, PORT_END, PORT_IN_BLOCK, EEPROM_OFFSET)
platform_dict_port = {'x86_64-mlnx_msn2010-r0': 3, 'x86_64-mlnx_msn2100-r0': 1, 'x86_64-mlnx_msn2410-r0': 2,
                      'x86_64-mlnx_msn2700-r0': 0, 'x86_64-mlnx_lssn2700': 0, 'x86_64-mlnx_msn2740-r0': 0,
                      'x86_64-mlnx_msn3420-r0': 5, 'x86_64-mlnx_msn3700-r0': 0, 'x86_64-mlnx_msn3700c-r0': 0,
                      'x86_64-mlnx_msn3800-r0': 4, 'x86_64-mlnx_msn4600-r0': 4, 'x86_64-mlnx_msn4600c-r0': 4,
                      'x86_64-mlnx_msn4700-r0': 0, 'x86_64-mlnx_msn4410-r0': 0}
port_position_tuple_list = [(0, 0, 31, 32, 1), (0, 0, 15, 16, 1), (0, 48, 55, 56, 1), (0, 18, 21, 22, 1), (0, 0, 63, 64, 1), (0, 48, 59, 60, 1)]

class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    # System status LED
    _led = None

    def __init__(self):
        super(Chassis, self).__init__()

        self.name = "Undefined"
        self.model = "Undefined"

        # Initialize Platform name
        self.platform_name = device_info.get_platform()

        # Initialize DMI data
        self.dmi_data = None
        
        # move the initialization of each components to their dedicated initializer
        # which will be called from platform
        #
        # Multiple scenarios need to be taken into consideration regarding the SFP modules initialization.
        # - Platform daemons
        #   - Can access multiple or all SFP modules
        # - sfputil
        #   - Sometimes can access only one SFP module
        #   - Call get_sfp to get one SFP module object
        #
        # We should initialize all SFP modules only if it is necessary because initializing SFP module is time-consuming.
        # This means,
        # - If get_sfp is called,
        #    - If the _sfp_list isn't initialized, initialize it first.
        #    - Only the SFP module being required should be initialized.
        # - If get_all_sfps is called,
        #    - If the _sfp_list isn't initialized, initialize it first.
        #    - All SFP modules need to be initialized.
        #      But the SFP modules that have already been initialized should not be initialized for the second time.
        #      This can caused by get_sfp being called before.
        #
        # Due to the complexity of SFP modules initialization, we have to introduce two initialized flags for SFP modules
        # - sfp_module_partial_initialized:
        #    - False: The _sfp_list is [] (SFP stuff has never been accessed)
        #    - True: The _sfp_list is a list whose length is number of SFP modules supported by the platform
        # - sfp_module_full_initialized:
        #    - False: All SFP modules have not been created
        #    - True: All SFP modules have been created
        #
        self.sfp_module_partial_initialized = False
        self.sfp_module_full_initialized = False
        self.sfp_event_initialized = False
        self.reboot_cause_initialized = False
        self.sdk_handle = None
        self.deinitialize_sdk_handle = None
        logger.log_info("Chassis loaded successfully")


    def __del__(self):
        if self.sfp_event_initialized:
            self.sfp_event.deinitialize()

        if self.deinitialize_sdk_handle:
            self.deinitialize_sdk_handle(self.sdk_handle)


    def initialize_psu(self):
        from sonic_platform.psu import Psu
        # Initialize PSU list
        self.psu_module = Psu
        for index in range(MLNX_NUM_PSU):
            psu = Psu(index, self.platform_name)
            self._psu_list.append(psu)


    def initialize_fan(self):
        from .device_data import DEVICE_DATA
        from sonic_platform.fan import Fan
        from .fan_drawer import RealDrawer, VirtualDrawer

        fan_data = DEVICE_DATA[self.platform_name]['fans']
        drawer_num = fan_data['drawer_num']
        drawer_type = fan_data['drawer_type']
        fan_num_per_drawer = fan_data['fan_num_per_drawer']
        drawer_ctor = RealDrawer if drawer_type == 'real' else VirtualDrawer
        fan_index = 0
        for drawer_index in range(drawer_num):
            drawer = drawer_ctor(drawer_index, fan_data)
            self._fan_drawer_list.append(drawer)
            for index in range(fan_num_per_drawer):
                fan = Fan(fan_index, drawer, index + 1)
                fan_index += 1
                drawer._fan_list.append(fan)


    def initialize_single_sfp(self, index):
        if not self._sfp_list[index]:
            if index >= self.QSFP_PORT_START and index < self.PORTS_IN_BLOCK:
                sfp_module = self.sfp_module(index, 'QSFP', self.get_sdk_handle, self.platform_name)
            else:
                sfp_module = self.sfp_module(index, 'SFP', self.get_sdk_handle, self.platform_name)

            self._sfp_list[index] = sfp_module


    def initialize_sfp(self, index=None):
        from sonic_platform.sfp import SFP

        self.sfp_module = SFP

        # Initialize SFP list
        port_position_tuple = self._get_port_position_tuple_by_platform_name()
        self.PORT_START = port_position_tuple[0]
        self.QSFP_PORT_START = port_position_tuple[1]
        self.PORT_END = port_position_tuple[2]
        self.PORTS_IN_BLOCK = port_position_tuple[3]

        if index is not None:
            if not self.sfp_module_partial_initialized:
                if index >= self.PORT_START and index < self.PORT_END:
                    self._sfp_list = list([None]*(self.PORT_END + 1))
                else:
                    raise IndexError("{} is not a valid index of SPF modules. Valid index range:[{}, {}]".format(
                        index, self.PORT_START + 1, self.PORT_END + 1))
                self.sfp_module_partial_initialized = True
        else:
            if not self.sfp_module_partial_initialized:
                self._sfp_list = list([None]*(self.PORT_END + 1))
                self.sfp_module_partial_initialized = True
            for index in range(self.PORT_START, self.PORT_END + 1):
                self.initialize_single_sfp(index)

            self.sfp_module_full_initialized = True


    def get_sdk_handle(self):
        if not self.sdk_handle:
            from sonic_platform.sfp import initialize_sdk_handle, deinitialize_sdk_handle
            self.sdk_handle = initialize_sdk_handle()
            if self.sdk_handle is None:
                logger.log_error('Failed to open SDK handle')
            else:
                self.deinitialize_sdk_handle = deinitialize_sdk_handle
        return self.sdk_handle


    def initialize_thermals(self):
        from sonic_platform.thermal import initialize_chassis_thermals
        # Initialize thermals
        initialize_chassis_thermals(self.platform_name, self._thermal_list)


    def initialize_eeprom(self):
        from .eeprom import Eeprom
        # Initialize EEPROM
        self._eeprom = Eeprom()
        # Get chassis name and model from eeprom
        self.name = self._eeprom.get_product_name()
        self.model = self._eeprom.get_part_number()


    def initialize_components(self):
        # Initialize component list
        from sonic_platform.component import ComponentONIE, ComponentSSD, ComponentBIOS, ComponentCPLD
        self._component_list.append(ComponentONIE())
        self._component_list.append(ComponentSSD())
        self._component_list.append(ComponentBIOS())
        self._component_list.extend(ComponentCPLD.get_component_list())

    def initizalize_system_led(self):
        from .led import SystemLed
        Chassis._led = SystemLed()


    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return self.name


    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        return self.model

    def get_revision(self):
        """
        Retrieves the hardware revision of the device
        
        Returns:
            string: Revision value of device
        """
        if self.dmi_data is None:
            self.dmi_data = self._parse_dmi(DMI_FILE)

        return self.dmi_data.get(DMI_VERSION, "N/A")
        
    ##############################################
    # SFP methods
    ##############################################
    def get_num_sfps(self):
        """
        Retrieves the number of sfps available on this chassis

        Returns:
            An integer, the number of sfps available on this chassis
        """
        if not self.sfp_module_full_initialized:
            self.initialize_sfp()
        return len(self._sfp_list)


    def get_all_sfps(self):
        """
        Retrieves all sfps available on this chassis

        Returns:
            A list of objects derived from SfpBase representing all sfps 
            available on this chassis
        """
        if not self.sfp_module_full_initialized:
            self.initialize_sfp()
        return self._sfp_list


    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>

        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
                   The index should be the sequence of a physical port in a chassis,
                   starting from 1.
                   For example, 1 for Ethernet0, 2 for Ethernet4 and so on.

        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None
        index -= 1

        try:
            if not self.sfp_module_partial_initialized:
                self.initialize_sfp(index)

            sfp = self._sfp_list[index]
            if not sfp:
                self.initialize_single_sfp(index)
                sfp = self._sfp_list[index]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (0-{})\n".format(
                             index, len(self._sfp_list)-1))

        return sfp


    def _extract_num_of_fans_and_fan_drawers(self):
        num_of_fan = 0
        num_of_drawer = 0
        for f in listdir(self.fan_path):
            if isfile(join(self.fan_path, f)):
                match_obj = re.match('fan(\d+)_speed_get', f)
                if match_obj != None:
                    if int(match_obj.group(1)) > num_of_fan:
                        num_of_fan = int(match_obj.group(1))
                else:
                    match_obj = re.match('fan(\d+)_status', f)
                    if match_obj != None and int(match_obj.group(1)) > num_of_drawer:
                        num_of_drawer = int(match_obj.group(1))

        return num_of_fan, num_of_drawer

    def _get_port_position_tuple_by_platform_name(self):
        position_tuple = port_position_tuple_list[platform_dict_port[self.platform_name]]
        return position_tuple


    def get_watchdog(self):
        """
        Retrieves hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device

        Note:
            We overload this method to ensure that watchdog is only initialized
            when it is referenced. Currently, only one daemon can open the watchdog.
            To initialize watchdog in the constructor causes multiple daemon 
            try opening watchdog when loading and constructing a chassis object
            and fail. By doing so we can eliminate that risk.
        """
        try:
            if self._watchdog is None:
                from sonic_platform.watchdog import get_watchdog
                self._watchdog = get_watchdog()
        except Exception as e:
            logger.log_info("Fail to load watchdog due to {}".format(repr(e)))

        return self._watchdog


    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.get_base_mac()


    def get_serial(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.get_serial_number()


    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis

        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.get_system_eeprom_info()


    def _read_generic_file(self, filename, len):
        """
        Read a generic file, returns the contents of the file
        """
        result = ''
        try:
            fileobj = io.open(filename)
            result = fileobj.read(len)
            fileobj.close()
            return result
        except Exception as e:
            logger.log_info("Fail to read file {} due to {}".format(filename, repr(e)))
            return '0'


    def _parse_dmi(self, filename):
        """
        Read DMI data chassis data and returns a dictionary of values

        Returns:
            A dictionary containing the dmi table of the switch chassis info
        """
        result = {}
        try:
            fileobj = open(filename, "rb")
            data = fileobj.read()
            fileobj.close()

            body = data[DMI_HEADER_LEN:]
            records = body.split(b'\x00')

            for k, v in DMI_TABLE_MAP.items():
                result[k] = records[v].decode("utf-8")

        except Exception as e:
            logger.log_error("Fail to decode DMI {} due to {}".format(filename, repr(e)))

        return result


    def _verify_reboot_cause(self, filename):
        '''
        Open and read the reboot cause file in 
        /var/run/hwmanagement/system (which is defined as REBOOT_CAUSE_ROOT)
        If a reboot cause file doesn't exists, returns '0'.
        '''
        return bool(int(self._read_generic_file(join(REBOOT_CAUSE_ROOT, filename), REBOOT_CAUSE_FILE_LENGTH).rstrip('\n')))


    def initialize_reboot_cause(self):
        self.reboot_major_cause_dict = {
            'reset_main_pwr_fail'       :   self.REBOOT_CAUSE_POWER_LOSS,
            'reset_aux_pwr_or_ref'      :   self.REBOOT_CAUSE_POWER_LOSS,
            'reset_asic_thermal'        :   self.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC,
            'reset_hotswap_or_wd'       :   self.REBOOT_CAUSE_WATCHDOG,
            'reset_swb_wd'              :   self.REBOOT_CAUSE_WATCHDOG,
            'reset_sff_wd'              :   self.REBOOT_CAUSE_WATCHDOG
        }
        self.reboot_minor_cause_dict = {
            'reset_fw_reset'            :   "Reset by ASIC firmware",
            'reset_long_pb'             :   "Reset by long press on power button",
            'reset_short_pb'            :   "Reset by short press on power button",
            'reset_comex_thermal'       :   "ComEx thermal shutdown",
            'reset_comex_pwr_fail'      :   "ComEx power fail",
            'reset_comex_wd'            :   "Reset requested from ComEx",
            'reset_from_asic'           :   "Reset requested from ASIC",
            'reset_reload_bios'         :   "Reset caused by BIOS reload",
            'reset_hotswap_or_halt'     :   "Reset caused by hotswap or halt",
            'reset_from_comex'          :   "Reset from ComEx",
            'reset_voltmon_upgrade_fail':   "Reset due to voltage monitor devices upgrade failure"
        }
        self.reboot_by_software = 'reset_sw_reset'
        self.reboot_cause_initialized = True


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
        #read reboot causes files in the following order
        if not self.reboot_cause_initialized:
            self.initialize_reboot_cause()

        for reset_file, reset_cause in self.reboot_major_cause_dict.items():
            if self._verify_reboot_cause(reset_file):
                return reset_cause, ''

        for reset_file, reset_cause in self.reboot_minor_cause_dict.items():
            if self._verify_reboot_cause(reset_file):
                return self.REBOOT_CAUSE_HARDWARE_OTHER, reset_cause

        if self._verify_reboot_cause(self.reboot_by_software):
            logger.log_info("Hardware reboot cause: the system was rebooted due to software requesting")
        else:
            logger.log_info("Hardware reboot cause: no hardware reboot cause found")

        return self.REBOOT_CAUSE_NON_HARDWARE, ''


    def _show_capabilities(self):
        """
        This function is for debug purpose
        Some features require a xSFP module to support some capabilities but it's unrealistic to
        check those modules one by one.
        So this function is introduce to show some capabilities of all xSFP modules mounted on the device.
        """
        for s in self._sfp_list:
            try:
                print("index {} tx disable {} dom {} calibration {} temp {} volt {} power (tx {} rx {})".format(s.index,
                    s.dom_tx_disable_supported,
                    s.dom_supported,
                    s.calibration,
                    s.dom_temp_supported,
                    s.dom_volt_supported,
                    s.dom_rx_power_supported,
                    s.dom_tx_power_supported
                    ))
            except:
                print("fail to retrieve capabilities for module index {}".format(s.index))


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
            timeout = MAX_SELECT_DELAY
            while True:
                status = self.sfp_event.check_sfp_status(port_dict, timeout)
                if bool(port_dict):
                    break
        else:
            status = self.sfp_event.check_sfp_status(port_dict, timeout)

        if status:
            self.reinit_sfps(port_dict)
            return True, {'sfp':port_dict}
        else:
            return True, {'sfp':{}}

    def reinit_sfps(self, port_dict):
        """
        Re-initialize SFP if there is any newly inserted SFPs
        :param port_dict: SFP event data
        :return:
        """
        # SFP not initialize yet, do nothing
        if not self.sfp_module_full_initialized:
            return

        from . import sfp
        for index, status in port_dict.items():
            if status == sfp.SFP_STATUS_INSERTED:
                try:
                    self.get_sfp(index).reinit()
                except Exception as e:
                    logger.log_error("Fail to re-initialize SFP {} - {}".format(index, repr(e)))

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
        return False if not Chassis._led else Chassis._led.set_status(color)

    def get_status_led(self):
        """
        Gets the state of the system LED

        Returns:
            A string, one of the valid LED color strings which could be vendor
            specified.
        """
        return None if not Chassis._led else Chassis._led.get_status()

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
