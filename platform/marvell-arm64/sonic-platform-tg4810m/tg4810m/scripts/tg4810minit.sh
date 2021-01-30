#!/bin/bash

# Platform init script for Delta TG4810M

# Load required kernel-mode drivers
load_kernel_drivers() {
    # Remove modules loaded during Linux init
    # FIX-ME: This will be removed in the future when Linux init no longer loads these
    rmmod i2c_mux_gpio
    rmmod i2c_dev
    rmmod i2c_mv64xxx

    # Carefully control the load order here to ensure consistent i2c bus numbering
    modprobe i2c_mv64xxx
    modprobe i2c_dev
    modprobe i2c_mux_gpio
    modprobe eeprom
}

# - Main entry

# Install kernel drivers required for i2c bus access
#load_kernel_drivers

# LOGIC to enumerate SFP eeprom devices - send 0x50 to kernel i2c driver - initialize devices
# the mux may be enumerated at number 4 or 5 so we check for the mux and skip if needed
# Get list of the mux channels
ismux_bus=$(i2cdetect -l|grep mux|cut -f1)
# Enumerate the SFP eeprom device on each mux channel
for mux in ${ismux_bus}
do
    echo optoe2 0x50 > /sys/class/i2c-adapter/${mux}/new_device
done

#choose PCA9546 channel 3 in order to collect present status
i2cset -y 0 0x70 0x00 0x08 
#select all the devices on PCA9546 i2c-2
i2cset -y 2 0x77 0x00 0x7
# Enable optical SFP Tx
i2cset -y  2 0x41 0x31 0x00
i2cset -y  2 0x41 0x32 0x00
i2cset -y  2 0x41 0x33 0x00
i2cset -y  2 0x41 0x34 0x00
i2cset -y  2 0x41 0x35 0x00
i2cset -y  2 0x41 0x36 0x00

echo "Delta-tg4810m - completed platform init script"
exit 0
