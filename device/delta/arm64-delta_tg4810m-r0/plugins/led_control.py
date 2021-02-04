#!/usr/bin/env python
# led_control.py
# Platform-specific LED control functionality for SONiC

try:
    from sonic_led.led_control_base import LedControlBase
    import time
    from socket import *
    from select import *
    import sonic_platform.platform
    import sonic_platform.chassis
except ImportError as e:
    raise ImportError(str(e) + " - required module not found")

smbus_present = 1
try:
    import smbus
except ImportError as e:
    smbus_present = 0

class LedControl(LedControlBase):
    """Platform specific LED control class"""
    def __init__(self):
        self.chassis = sonic_platform.platform.Platform().get_chassis()
        self._initDefaultConfig()

    def _initDefaultConfig(self):
        self._initLed()

    def gpio_led_write(self,gpio_led_path, value):
        try:
            gpio_file = open(gpio_led_path + "/brightness", 'w')
            print(gpio_led_path)
            gpio_file.write(str(value))
            gpio_file.close
        except IOError as e:
            print "error: unable to open gpio file: %s" % str(e)
    
    def _initLed(self):
        # Front Panel LEDs setting
        fan_led=0xf
        psu_led=0xf
        sys_led=0xf

        while True:
            # Front Panel FAN LED
            if ( self.chassis.get_fan(0).get_status() == self.chassis.get_fan(1).get_status() == self.chassis.get_fan(2).get_status() == True ):
                if ( fan_led != 0x1 ):
                    	self.gpio_led_write("/sys/class/leds/fanLedGreen",1)
                    	self.gpio_led_write("/sys/class/leds/fanLedAmber",0)
                    	fan_led = 0x1
            else :
                if ( fan_led != 0x0 ):
                    	self.gpio_led_write("/sys/class/leds/fanLedAmber",1)
                    	self.gpio_led_write("/sys/class/leds/fanLedGreen",0)
                    	fan_led = 0x0
            
	    # Front Panel PSU LED
            if ( self.chassis.get_psu(0).get_status() == self.chassis.get_psu(1).get_status() == True ):
                if ( psu_led != 0x1 ):
                    	self.gpio_led_write("/sys/class/leds/psuLedGreen",1)
                    	self.gpio_led_write("/sys/class/leds/psuLedAmber",0)
                    	psu_led = 0x1
            else :
                if ( psu_led != 0x0 ):
                    	self.gpio_led_write("/sys/class/leds/psuLedAmber",1)
                    	self.gpio_led_write("/sys/class/leds/psuLedGreen",0)
                    	psu_led = 0x0
            
	    # Front Panel system LED
            if ( fan_led == psu_led == 0x1 ) :
                if ( sys_led != 0x1 ):
                    	self.gpio_led_write("/sys/class/leds/sysLedGreen",1)
                    	self.gpio_led_write("/sys/class/leds/sysLedAmber",0)
                    	sys_led = 0x1
            else:
                if ( sys_led != 0x0 ):
                    	self.gpio_led_write("/sys/class/leds/sysLedAmber",1)
                    	self.gpio_led_write("/sys/class/leds/sysLedGreen",0)
                    	sys_led = 0x0

            time.sleep(6)

    # Helper method to map SONiC port name to index
    def _port_name_to_index(self, port_name):
        # Strip "Ethernet" off port name
        if not port_name.startswith(self.SONIC_PORT_NAME_PREFIX):
            return -1
        port_idx = int(port_name[len(self.SONIC_PORT_NAME_PREFIX):])
        return port_idx

    # called when port states change- implementation of port_link_state_change() method if needed
    def port_link_state_change(self, portname, state):
        return
