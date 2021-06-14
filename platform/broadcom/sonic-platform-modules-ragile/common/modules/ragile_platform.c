/*
 * ragile_platform.c - A driver for ragile platform module
 *
 * Copyright (c) 2019  <support@ragile.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sysfs.h>
#include <linux/slab.h>
#include <linux/stat.h>
#include <linux/uaccess.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/i2c.h>
#include <linux/i2c-mux.h>
#include <linux/platform_data/i2c-gpio.h>
#include <linux/platform_device.h>
#include <linux/delay.h>
#include <linux/i2c-smbus.h>
#include <linux/string.h>

#define PLATFORM_I2C_RETRY_TIMES (3)

s32 platform_i2c_smbus_read_byte_data(const struct i2c_client *client, u8 command)
{
	int try;
	s32 ret;

	ret = -1;
	for (try = 0; try < PLATFORM_I2C_RETRY_TIMES; try ++) {
		if ((ret = i2c_smbus_read_byte_data(client, command)) >= 0)
			break;
	}
	return ret;
}
EXPORT_SYMBOL(platform_i2c_smbus_read_byte_data);

s32 platform_i2c_smbus_read_i2c_block_data(const struct i2c_client *client,
					   u8 command, u8 length, u8 *values)
{
	int try ;
	s32 ret;

	ret = -1;
	for (try = 0; try < PLATFORM_I2C_RETRY_TIMES; try ++) {
		if ((ret = i2c_smbus_read_i2c_block_data(client, command, length, values)) >= 0)
			break;
	}
	return ret;
}
EXPORT_SYMBOL(platform_i2c_smbus_read_i2c_block_data);

s32 platform_i2c_smbus_read_word_data(const struct i2c_client *client, u8 command)
{
	int try;
	s32 ret;

	ret = -1;
	for (try = 0; try < PLATFORM_I2C_RETRY_TIMES; try ++) {
		if ((ret = i2c_smbus_read_word_data(client, command)) >= 0)
			break;
	}
	return ret;
}
EXPORT_SYMBOL(platform_i2c_smbus_read_word_data);

static int __init ragile_platform_init(void)
{
	return 0;
}

static void __exit ragile_platform_exit(void)
{
	return;
}

module_init(ragile_platform_init);
module_exit(ragile_platform_exit);

MODULE_DESCRIPTION("ragile Platform Support");
MODULE_AUTHOR("support <support@ragile.com>");
MODULE_LICENSE("GPL");
