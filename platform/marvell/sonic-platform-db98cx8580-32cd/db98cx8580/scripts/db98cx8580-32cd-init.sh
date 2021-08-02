#!/bin/bash

# Platform init script for db98cx8580-32cd 


# - Main entry
# LOGIC to enumerate SFP eeprom devices - send 0x50 to kernel i2c driver - initialize devices
echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-2/new_device

exit 0
