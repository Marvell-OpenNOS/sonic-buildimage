#!/bin/bash

fw_uboot_env_cfg()
{
    echo "Setting up U-Boot environment..."

    MACH_FILE="/host/machine.conf"
    PLATFORM=`sed -n 's/onie_platform=\(.*\)/\1/p' $MACH_FILE`

    if [ "$PLATFORM" = "arm64-delta_tg4810m-r0" ]; then
	# TG410M  board Uboot ENV offset
        FW_ENV_DEFAULT='/dev/mtd1  0x00000000  0x00010000 0x00001000'
        echo "Using pre-configured uboot env"
        echo $FW_ENV_DEFAULT > /etc/fw_env.config
    fi
}


main()
{
    fw_uboot_env_cfg
    echo "Delta-TG4810M: /dev/mtd0 FW_ENV_DEFAULT"
}

main $@
