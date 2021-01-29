#!/bin/bash

fw_uboot_env_cfg()
{
    echo "Setting up U-Boot environment..."
    MACH_FILE="/host/machine.conf"
    PLATFORM=`sed -n 's/onie_platform=\(.*\)/\1/p' $MACH_FILE`
    if [ "$PLATFORM" = "arm64-delta_tg48m_poe-r0" ]; then
	# TG48M-P  board Uboot ENV offset
        FW_ENV_DEFAULT='/dev/mtd1 00010000 00001000 '

        demo_part=$(sgdisk -p /dev/sda | grep -e "SONiC-OS")
        if [ -z "$demo_part" ]; then
            FW_ENV_DEFAULT='/dev/mtd1 00010000 00001000  8'
        fi
    else
        FW_ENV_DEFAULT='/dev/mtd1 00010000 00001000 8'
    fi
    echo "Using pre-configured uboot env"
    echo $FW_ENV_DEFAULT > /etc/fw_env.config
}


main()
{
    fw_uboot_env_cfg
    echo "Delta-TG48M-P: /dev/mtd0 FW_ENV_DEFAULT"
}

main $@
