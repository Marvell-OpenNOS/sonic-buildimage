########################################################################
# Module contains an implementation of SONiC Platform Base API and
# provides the Thermals' information which are available in the platform
########################################################################


try:
    import os
    from sonic_platform_base.thermal_base import ThermalBase
    from sonic_py_common import logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

sonic_logger = logger.Logger('thermal')

class Thermal(ThermalBase):
    """ET6448M platform-specific Thermal class"""

    I2C_CLASS_DIR = "/sys/class/i2c-adapter/"
    I2C_DEV_MAPPING = (['i2c-0/0-004a/hwmon/', 1],
                       ['i2c-0/0-004b/hwmon/', 1],
                       ['i2c-0/0-002e/', 1],
                       ['i2c-0/0-002e/', 2],
                       ['i2c-0/0-002e/', 3])

    HWMON_CLASS_DIR = "/sys/class/hwmon/"

    THERMAL_NAME = ("PCB PHY", "PCB MAC",
                    "ADT7473-CPU", "ADT7473-LOC", "ADT7473-MAC",
                    "CPU Core")

    def __init__(self, thermal_index):
        self.index = thermal_index + 1
        self.is_psu_thermal = False
        self.dependency = None
        self.thermal_high_threshold_file = None
        # PCB temperature sensors
        if self.index < 3:
            i2c_path = self.I2C_CLASS_DIR + self.I2C_DEV_MAPPING[self.index - 1][0]
            sensor_index = self.I2C_DEV_MAPPING[self.index - 1][1]
            sensor_max_suffix = "max"
            sensor_crit_suffix = None
            hwmon_node = os.listdir(i2c_path)[0]
            self.SENSOR_DIR = i2c_path + hwmon_node + '/'

        # ADT7473 temperature sensors
        elif self.index < 6:
            i2c_path = self.I2C_CLASS_DIR + self.I2C_DEV_MAPPING[self.index - 1][0]
            sensor_index = self.I2C_DEV_MAPPING[self.index - 1][1]
            sensor_max_suffix = "max"
            sensor_crit_suffix = "crit"
            self.SENSOR_DIR = i2c_path

        # Armada 38x SOC temperature sensor
        else:
            dev_path = self.HWMON_CLASS_DIR
            sensor_index = 0
            sensor_max_suffix = None
            sensor_crit_suffix = None
            hwmon_node = os.listdir(dev_path)[0]
            self.SENSOR_DIR = dev_path + hwmon_node + '/'

        # sysfs file for current temperature value
        self.thermal_temperature_file = self.SENSOR_DIR \
            + "temp{}_input".format(sensor_index)

        # sysfs file for high threshold value if supported for this sensor
        if sensor_max_suffix:
            self.thermal_high_threshold_file = self.SENSOR_DIR \
                + "temp{}_{}".format(sensor_index, sensor_max_suffix)
        else:
            self.thermal_high_threshold_file = None

        # sysfs file for crit high threshold value if supported for this sensor
        if sensor_crit_suffix:
            self.thermal_high_crit_threshold_file = self.SENSOR_DIR \
                + "temp{}_{}".format(sensor_index, sensor_crit_suffix)
        else:
            self.thermal_high_crit_threshold_file = None

    def _read_sysfs_file(self, sysfs_file):
        # On successful read, returns the value read from given
        # sysfs_file and on failure returns 'ERR'
        rv = 'ERR'

        if (not os.path.isfile(sysfs_file)):
            return rv

        try:
            with open(sysfs_file, 'r') as fd:
                rv = fd.read()
        except Exception as e:
            rv = 'ERR'

        rv = rv.rstrip('\r\n')
        rv = rv.lstrip(" ")
        return rv

    def get_name(self):
        """
        Retrieves the name of the thermal

        Returns:
            string: The name of the thermal
        """
        return self.THERMAL_NAME[self.index - 1]

    def get_presence(self):
        """
        Retrieves the presence of the thermal

        Returns:
            bool: True if thermal is present, False if not
        """
        if self.dependency:
            return self.dependency.get_presence()
        else:
            return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the Thermal

        Returns:
            string: Model/part number of Thermal
        """
        return 'NA'

    def get_serial(self):
        """
        Retrieves the serial number of the Thermal

        Returns:
            string: Serial number of Thermal
        """
        return 'NA'

    def get_status(self):
        """
        Retrieves the operational status of the thermal

        Returns:
            A boolean value, True if thermal is operating properly,
            False if not
        """
        if self.dependency:
            return self.dependency.get_status()
        else:
            return True

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal

        Returns:
            A float number of current temperature in Celsius up to
            nearest thousandth of one degree Celsius, e.g. 30.125
        """
        thermal_temperature = self._read_sysfs_file(
            self.thermal_temperature_file)
        if (thermal_temperature != 'ERR'):
            thermal_temperature = float(thermal_temperature) / 1000
        else:
            thermal_temperature = 0

        return float("{:.3f}".format(thermal_temperature))

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal

        Returns:
            A float number, the high threshold temperature of thermal in
            Celsius up to nearest thousandth of one degree Celsius,
            e.g. 30.125
        """
        # Not implemented for this sensor
        if not self.thermal_high_threshold_file:
            raise  NotImplementedError

        thermal_high_threshold = self._read_sysfs_file(
            self.thermal_high_threshold_file)
        if (thermal_high_threshold != 'ERR'):
            thermal_high_threshold = float(thermal_high_threshold) / 1000
        else:
            thermal_high_threshold = 0.0

        return float("{:.3f}".format(thermal_high_threshold))

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal

        Args :
            temperature: A float number up to nearest thousandth of one
            degree Celsius, e.g. 30.125
        Returns:
            A boolean, True if threshold is set successfully, False if
            not
        """
        # Thermal threshold values are pre-defined based on HW.
        return False

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal

        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """

        # Not implemented for this sensor
        if not self.thermal_high_crit_threshold_file:
            raise  NotImplementedError

        thermal_high_crit_threshold = self._read_sysfs_file(
            self.thermal_high_crit_threshold_file)
        if (thermal_high_crit_threshold != 'ERR'):
            thermal_high_crit_threshold = float(thermal_high_crit_threshold) / 1000
        else:
            thermal_high_crit_threshold = 0.0

        return float("{:.3f}".format(thermal_high_crit_threshold))

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
        return False
