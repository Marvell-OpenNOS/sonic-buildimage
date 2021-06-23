########################################################################
# ET6448M
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs' information which are available in the platform
#
########################################################################

try:
    import sys
    from sonic_platform_base.psu_base import PsuBase
    from sonic_py_common import logger
    from sonic_platform.eeprom import Eeprom
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

sonic_logger = logger.Logger('psu')

class Psu(PsuBase):
    """Platform-specific PSU class for et6448m """

    def __init__(self, psu_index):
        # PSU is 1-based in et6448m platforms
        self.index = psu_index + 1
        self._fan_list = []

        # PSU eeprom
        self.eeprom = Eeprom(is_psu=True, psu_index=self.index)

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

        if smbus_present == 0:  # if called from psuutil outside of pmon
            cmdstatus, psustatus = cmd.getstatusoutput('sudo i2cget -y 0 0x41 0xa')
            psustatus = int(psustatus, 16)
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0xa
            psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus & 1
            if psustatus == 1:
                return True
        if self.index == 2:
            psustatus = psustatus & 2
            if psustatus == 2:
                return True

        return False

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


    def get_part_number(self):
        """
        Retrieves the part number of the PSU

        Returns:
            string: Part number of PSU
        """
        return self.eeprom.part_number_str()

    def get_status(self):
        """
        Retrieves the operational status of the PSU

        Returns:
            bool: True if PSU is operating properly, False if not
        """

        if smbus_present == 0:
            cmdstatus, psustatus = cmd.getstatusoutput('sudo i2cget -y 0 0x41 0xa')
            psustatus = int(psustatus, 16)
            sonic_logger.log_warning("PMON psu-smbus - presence = 0 ")
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0xa
            psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus & 4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus & 8
            if psustatus == 8:
                return True

        return False

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        if smbus_present == 0:
            cmdstatus, psustatus = cmd.getstatusoutput('sudo i2cget -y 0 0x41 0xa')
            psustatus = int(psustatus, 16)
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0xa
            psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus & 4
            if psustatus == 4:
                psu_voltage = 12.0
                return psu_voltage
        if self.index == 2:
            psustatus = psustatus & 8
            if psustatus == 8:
                psu_voltage = 12.0
                return psu_voltage

        psu_voltage = 0.0
        return psu_voltage

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device
        Returns:
            integer: The 1-based relative physical position in parent device
        """
        return self.index

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and
            passed all its internal self-tests, False if not.
        """

        if smbus_present == 0:
            cmdstatus, psustatus = cmd.getstatusoutput('sudo i2cget -y 0 0x41 0xa')
            psustatus = int(psustatus, 16)
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0xa
            psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        if self.index == 1:
            psustatus = psustatus & 4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus & 8
            if psustatus == 8:
                return True

        return False

    def get_status_led(self):
        """
        Gets the state of the PSU status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if self.get_powergood_status():
            return self.STATUS_LED_COLOR_GREEN
        else:
            return self.STATUS_LED_COLOR_OFF

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
        # The firmware running in the PSU controls the LED
        # and the PSU LED state cannot be changed from CPU.
        return False
