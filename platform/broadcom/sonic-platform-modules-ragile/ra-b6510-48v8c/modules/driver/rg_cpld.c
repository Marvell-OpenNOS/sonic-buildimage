/*
 * rg_cpld.c - A driver for cpld
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
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/jiffies.h>
#include <linux/i2c.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/err.h>
#include <linux/mutex.h>
#include <linux/fs.h>
#include <linux/uaccess.h>


/* debug level */
typedef enum {
	DBG_START,
	DBG_VERBOSE,
	DBG_KEY,
	DBG_WARN,
	DBG_ERROR,
	DBG_END,
} dbg_level_t;

static int debuglevel = 0;
module_param(debuglevel, int, S_IRUGO);

#define DBG_DEBUG(fmt, arg...)  do { \
	if ( debuglevel > DBG_START && debuglevel < DBG_ERROR) { \
		printk(KERN_INFO "[DEBUG]:<%s, %d>:"fmt, __FUNCTION__, __LINE__, ##arg); \
	} else if ( debuglevel >= DBG_ERROR ) {   \
		printk(KERN_ERR "[DEBUG]:<%s, %d>:"fmt, __FUNCTION__, __LINE__, ##arg); \
	} else {    } \
} while (0)

#define DBG_ERROR(fmt, arg...)  do { \
	if ( debuglevel > DBG_START) {  \
		printk(KERN_ERR "[ERROR]:<%s, %d>:"fmt, __FUNCTION__, __LINE__, ##arg); \
	} \
} while (0)

static const unsigned short rg_i2c_cpld[] = { 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, I2C_CLIENT_END };

#define CPLD_SIZE 256
#define CPLD_I2C_RETRY_TIMES 3
#define READ_TEMP_FAIL 1000000

struct cpld_data {
	struct i2c_client *client;
	struct device *hwmon_dev;
	struct mutex update_lock;
	char valid;                 /* !=0 if registers are valid */
	unsigned long last_updated; /* In jiffies */
	u8 data[CPLD_SIZE];         /* Register value */
};

static s32 cpld_i2c_smbus_read_byte_data(const struct i2c_client *client, u8 command)
{
	int try;
	s32 ret;

	ret = -1;
	for (try = 0; try < CPLD_I2C_RETRY_TIMES; try++) {
		if ((ret = i2c_smbus_read_byte_data(client, command) ) >= 0 )
			break;
	}
	return ret;
}

static s32 cpld_i2c_smbus_read_i2c_block_data(const struct i2c_client *client,
		u8 command, u8 length, u8 *values)
{
	int try;
	s32 ret;

	ret = -1;
	for (try = 0; try < CPLD_I2C_RETRY_TIMES; try++) {
		if ((ret = i2c_smbus_read_i2c_block_data(client, command, length, values) ) >= 0 )
			break;
	}
	return ret;
}

static ssize_t show_fan_rpm_value(struct device *dev, struct device_attribute *da, char *buf)
{
	struct cpld_data *data = dev_get_drvdata(dev);
	struct i2c_client *client = data->client;
	int index = to_sensor_dev_attr_2(da)->index;
	uint8_t size;
	s32 status;
	s32 ret_t;

	ret_t = 0;
	status = -1;
	size = 0;
	mutex_lock(&data->update_lock);
	status = cpld_i2c_smbus_read_byte_data(client, index);
	if (status < 0) {
		mutex_unlock(&data->update_lock);
		return 0;
	}
	data->data[0] = status;
	status = cpld_i2c_smbus_read_byte_data(client, index + 1);
	if (status < 0) {
		mutex_unlock(&data->update_lock);
		return 0;
	}
	data->data[1] = status;
	DBG_DEBUG("cpld reg pos:0x%x value:0x%x\n",  index, data->data[0]);
	DBG_DEBUG("cpld reg pos:0x%x value:0x%x\n",  index + 1, data->data[1]);
	ret_t = (data->data[1] << 8) + data->data[0] ;
	if (ret_t == 0 ) {
		size = snprintf(buf, CPLD_SIZE, "%d\n", ret_t);
	} else if (ret_t == 0xffff) {
		size = snprintf(buf, CPLD_SIZE, "%d\n", 0);
	} else {
		size = snprintf(buf, CPLD_SIZE, "%d\n", 15000000 / ret_t);
	}
	mutex_unlock(&data->update_lock);
	return size;
}

static ssize_t set_cpld_sysfs_value(struct device *dev, struct device_attribute *da, const char *buf, size_t 
count)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct i2c_client *client = to_i2c_client(dev);
	struct cpld_data *data = i2c_get_clientdata(client);
	unsigned long val;
	int err;

	err = kstrtoul(buf, 16, &val);
	if (err)
		return err;
	if ((val < 0) || (val > 0xff)) {
		DBG_ERROR("please enter 0x00 ~ 0xff\n");
		return -1;
	}
	mutex_lock(&data->update_lock);
	data->data[0] = (u8)val;
	DBG_DEBUG("pos: 0x%02x count = %ld, data = 0x%02x\n", attr->index, count, data->data[0]);
	i2c_smbus_write_byte_data(client, attr->index, data->data[0]);
	mutex_unlock(&data->update_lock);

	return count;
}

static ssize_t show_cpld_version(struct device *dev, struct device_attribute *da, char *buf)
{
	struct i2c_client *client = to_i2c_client(dev);
	struct cpld_data *data = i2c_get_clientdata(client);
	s32 status;

	status = -1;
	mutex_lock(&data->update_lock);
	status = cpld_i2c_smbus_read_i2c_block_data(client, 0, 4, data->data);
	if (status < 0) {
		mutex_unlock(&data->update_lock);
		return 0;
	}
	mutex_unlock(&data->update_lock);
	return sprintf(buf, "%02x %02x %02x %02x \n", data->data[0], data->data[1], data->data[2], 
	data->data[3]);
}

static ssize_t show_cpld_sysfs_value(struct device *dev, struct device_attribute *da, char *buf)
{
	struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
	struct i2c_client *client = to_i2c_client(dev);
	struct cpld_data *data = i2c_get_clientdata(client);
	s32 status;

	status = -1;
	mutex_lock(&data->update_lock);
	status = cpld_i2c_smbus_read_byte_data(client, attr->index);
	if (status < 0) {
		mutex_unlock(&data->update_lock);
		return 0;
	}
	data->data[0]  = status;
	DBG_DEBUG("cpld reg pos:0x%x value:0x%02x\n", attr->index, data->data[0]);
	mutex_unlock(&data->update_lock);
	return sprintf(buf, "%02x\n", data->data[0]);
}

static ssize_t show_mac_temp_value(struct device *dev, struct device_attribute *da, char *buf)
{
    struct cpld_data *data = dev_get_drvdata(dev);
    struct i2c_client *client = data->client;
    int index = to_sensor_dev_attr_2(da)->index;
    int tmp_value, value;
    s32 status;

    status = -1;
    mutex_lock(&data->update_lock);

    status = cpld_i2c_smbus_read_byte_data(client, index);
    if (status < 0) {
        mutex_unlock(&data->update_lock);
        return snprintf(buf, CPLD_SIZE, "%d\n", -READ_TEMP_FAIL);
    }
    data->data[0] = status;
    status = cpld_i2c_smbus_read_byte_data(client, index + 1);
    if (status < 0) {
        mutex_unlock(&data->update_lock);
        return snprintf(buf, CPLD_SIZE, "%d\n", -READ_TEMP_FAIL);
    }
    data->data[1] = status;
    DBG_DEBUG("cpld reg pos:0x%x value:0x%x\n", index, data->data[0]);
    DBG_DEBUG("cpld reg pos:0x%x value:0x%x\n", index + 1, data->data[1]);
    mutex_unlock(&data->update_lock);

    tmp_value = (data->data[1] << 8) + data->data[0];
    if (tmp_value == 0) {
        DBG_ERROR("invalid cpld value : %d.\n", tmp_value);
        return snprintf(buf, CPLD_SIZE, "%d\n", -READ_TEMP_FAIL);
    }
    
    DBG_DEBUG("tmp_value = 0x%x\n", tmp_value);
    value = 434100 - (12500000 / (tmp_value * 100 - 1) *535);
    if ((value / 1000 < -70) || (value / 1000 > 200)) {
        return snprintf(buf, CPLD_SIZE, "%d\n", -READ_TEMP_FAIL);
    }

    return snprintf(buf, CPLD_SIZE, "%d\n", value);
    
}

/* common */
static SENSOR_DEVICE_ATTR(cpld_version, S_IRUGO | S_IWUSR, show_cpld_version, NULL, 0);

/*0x37 hwmon*/
static SENSOR_DEVICE_ATTR(fan1_input, S_IRUGO | S_IWUSR ,show_fan_rpm_value, NULL, 0x1B);
static SENSOR_DEVICE_ATTR(fan2_input, S_IRUGO | S_IWUSR ,show_fan_rpm_value, NULL, 0x1D);
static SENSOR_DEVICE_ATTR(fan3_input, S_IRUGO | S_IWUSR ,show_fan_rpm_value, NULL, 0x1F);
static SENSOR_DEVICE_ATTR(fan4_input, S_IRUGO | S_IWUSR ,show_fan_rpm_value, NULL, 0x21);

/* 0x32 */
static SENSOR_DEVICE_ATTR(fan_speed_set, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x15);
static SENSOR_DEVICE_ATTR(fan0_led, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x23);
static SENSOR_DEVICE_ATTR(fan1_led, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x24);
static SENSOR_DEVICE_ATTR(fan2_led, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x25);
static SENSOR_DEVICE_ATTR(fan3_led, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x26);

/* 0x37 */
static SENSOR_DEVICE_ATTR(fan_present, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, NULL, 0x30);
static SENSOR_DEVICE_ATTR(fan_status, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, NULL, 0x31);
static SENSOR_DEVICE_ATTR(psu_status, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, NULL, 0x51);
static SENSOR_DEVICE_ATTR(broad_back_lct, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x2a);
static SENSOR_DEVICE_ATTR(broad_back_sys, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xb2);

/* 0x33 */
static SENSOR_DEVICE_ATTR(mac_led, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa0);
static SENSOR_DEVICE_ATTR(broad_front_lct, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x2a);
static SENSOR_DEVICE_ATTR(broad_front_bmc, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xb1);
static SENSOR_DEVICE_ATTR(broad_front_cpu, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xb2);
static SENSOR_DEVICE_ATTR(broad_front_pwr, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xb3);
static SENSOR_DEVICE_ATTR(broad_front_fan, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xb4);
static SENSOR_DEVICE_ATTR(sfp_led1_yellow, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xad);
static SENSOR_DEVICE_ATTR(mac_temp_flag, S_IRUGO, show_cpld_sysfs_value, NULL, 0xd4);

/* 0x34 */
static SENSOR_DEVICE_ATTR(sfp_presence1, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, NULL, 0x30);
static SENSOR_DEVICE_ATTR(sfp_presence2, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, NULL, 0x31);
static SENSOR_DEVICE_ATTR(sfp_presence3, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, NULL, 0x32);

static SENSOR_DEVICE_ATTR(sfp_enable, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa1);
static SENSOR_DEVICE_ATTR(sfp_led1, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa2);
static SENSOR_DEVICE_ATTR(sfp_led2, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa3);
static SENSOR_DEVICE_ATTR(sfp_led3, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa4);
static SENSOR_DEVICE_ATTR(sfp_led_flash1, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa5);
static SENSOR_DEVICE_ATTR(sfp_led_flash2, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa6);
static SENSOR_DEVICE_ATTR(sfp_led_flash3, S_IRUGO | S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa7);
static SENSOR_DEVICE_ATTR(sfp_txdis1, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x60);
static SENSOR_DEVICE_ATTR(sfp_txdis2, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x61);
static SENSOR_DEVICE_ATTR(sfp_txdis3, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0x62);

static SENSOR_DEVICE_ATTR(port_speed1, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc0);
static SENSOR_DEVICE_ATTR(port_speed2, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc1);
static SENSOR_DEVICE_ATTR(port_speed3, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc2);
static SENSOR_DEVICE_ATTR(port_speed4, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc3);
static SENSOR_DEVICE_ATTR(port_speed5, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc4);
static SENSOR_DEVICE_ATTR(port_speed6, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc5);

/* 0x35 */
static SENSOR_DEVICE_ATTR(sfp_enable2, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa0);
static SENSOR_DEVICE_ATTR(sfp_led2_yellow, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xad);
static SENSOR_DEVICE_ATTR(mac_temp_input, S_IRUGO, show_mac_temp_value, NULL, 0xca);

/* 0x36 */
static SENSOR_DEVICE_ATTR(sfp_presence4, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, NULL, 0x30);
static SENSOR_DEVICE_ATTR(sfp_presence5, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, NULL, 0x31);
static SENSOR_DEVICE_ATTR(sfp_presence6, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, NULL, 0x32);
static SENSOR_DEVICE_ATTR(sfp_presence7, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, NULL, 0x33);
static SENSOR_DEVICE_ATTR(sfp_led4, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa2);
static SENSOR_DEVICE_ATTR(sfp_led5, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa3);
static SENSOR_DEVICE_ATTR(sfp_led6, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa4);
static SENSOR_DEVICE_ATTR(sfp_led7, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa5);
static SENSOR_DEVICE_ATTR(sfp_led_flash4, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa6);
static SENSOR_DEVICE_ATTR(sfp_led_flash5, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa7);
static SENSOR_DEVICE_ATTR(sfp_led_flash6, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa8);
static SENSOR_DEVICE_ATTR(sfp_led_flash7, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0xa9);

static SENSOR_DEVICE_ATTR(sfp_txdis4, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0x60);
static SENSOR_DEVICE_ATTR(sfp_txdis5, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0x61);
static SENSOR_DEVICE_ATTR(sfp_txdis6, S_IRUGO | S_IWUSR ,show_cpld_sysfs_value, set_cpld_sysfs_value, 0x62);

static SENSOR_DEVICE_ATTR(port_speed7, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc0);
static SENSOR_DEVICE_ATTR(port_speed8, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc1);
static SENSOR_DEVICE_ATTR(port_speed9, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc2);
static SENSOR_DEVICE_ATTR(port_speed10, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc3);
static SENSOR_DEVICE_ATTR(port_speed11, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc4);
static SENSOR_DEVICE_ATTR(port_speed12, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc5);
static SENSOR_DEVICE_ATTR(port_speed13, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc6);
static SENSOR_DEVICE_ATTR(port_speed14, S_IRUGO| S_IWUSR, show_cpld_sysfs_value, set_cpld_sysfs_value, 0xc7);

static struct attribute *cpld32_sysfs_attrs[] = {
	&sensor_dev_attr_fan_speed_set.dev_attr.attr,
	&sensor_dev_attr_fan0_led.dev_attr.attr,
	&sensor_dev_attr_fan1_led.dev_attr.attr,
	&sensor_dev_attr_fan2_led.dev_attr.attr,
	&sensor_dev_attr_fan3_led.dev_attr.attr,
	NULL
};

static struct attribute *cpld37_sysfs_attrs[] = {
	&sensor_dev_attr_fan_present.dev_attr.attr,
	&sensor_dev_attr_fan_status.dev_attr.attr,
	&sensor_dev_attr_psu_status.dev_attr.attr,
	&sensor_dev_attr_broad_back_lct.dev_attr.attr,
	&sensor_dev_attr_broad_back_sys.dev_attr.attr,
	&sensor_dev_attr_cpld_version.dev_attr.attr,
	NULL
};

static struct attribute *cpld33_sysfs_attrs[] = {
	&sensor_dev_attr_mac_led.dev_attr.attr,
	&sensor_dev_attr_broad_front_lct.dev_attr.attr,
	&sensor_dev_attr_broad_front_bmc.dev_attr.attr,
	&sensor_dev_attr_broad_front_cpu.dev_attr.attr,
	&sensor_dev_attr_broad_front_pwr.dev_attr.attr,
	&sensor_dev_attr_broad_front_fan.dev_attr.attr,
	&sensor_dev_attr_sfp_led1_yellow.dev_attr.attr,
	&sensor_dev_attr_mac_temp_flag.dev_attr.attr,
	&sensor_dev_attr_cpld_version.dev_attr.attr,
	NULL
};

static struct attribute *cpld34_sysfs_attrs[] = {
	&sensor_dev_attr_sfp_presence1.dev_attr.attr,
	&sensor_dev_attr_sfp_presence2.dev_attr.attr,
	&sensor_dev_attr_sfp_presence3.dev_attr.attr,
	&sensor_dev_attr_sfp_enable.dev_attr.attr,
	&sensor_dev_attr_sfp_led1.dev_attr.attr,
	&sensor_dev_attr_sfp_led2.dev_attr.attr,
	&sensor_dev_attr_sfp_led3.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash1.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash2.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash3.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis1.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis2.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis3.dev_attr.attr,
	&sensor_dev_attr_port_speed1.dev_attr.attr,
	&sensor_dev_attr_port_speed2.dev_attr.attr,
	&sensor_dev_attr_port_speed3.dev_attr.attr,
	&sensor_dev_attr_port_speed4.dev_attr.attr,
	&sensor_dev_attr_port_speed5.dev_attr.attr,
	&sensor_dev_attr_port_speed6.dev_attr.attr,
	NULL
};

static struct attribute *cpld36_sysfs_attrs[] = {
	&sensor_dev_attr_sfp_presence4.dev_attr.attr,
	&sensor_dev_attr_sfp_presence5.dev_attr.attr,
	&sensor_dev_attr_sfp_presence6.dev_attr.attr,
	&sensor_dev_attr_sfp_presence7.dev_attr.attr,
	&sensor_dev_attr_sfp_led4.dev_attr.attr,
	&sensor_dev_attr_sfp_led5.dev_attr.attr,
	&sensor_dev_attr_sfp_led6.dev_attr.attr,
	&sensor_dev_attr_sfp_led7.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash4.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash5.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash6.dev_attr.attr,
	&sensor_dev_attr_sfp_led_flash7.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis4.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis5.dev_attr.attr,
	&sensor_dev_attr_sfp_txdis6.dev_attr.attr,
	&sensor_dev_attr_port_speed7.dev_attr.attr,
	&sensor_dev_attr_port_speed8.dev_attr.attr,
	&sensor_dev_attr_port_speed9.dev_attr.attr,
	&sensor_dev_attr_port_speed10.dev_attr.attr,
	&sensor_dev_attr_port_speed11.dev_attr.attr,
	&sensor_dev_attr_port_speed12.dev_attr.attr,
	&sensor_dev_attr_port_speed13.dev_attr.attr,
	&sensor_dev_attr_port_speed14.dev_attr.attr,
	NULL
};

static struct attribute *cpld35_sysfs_attrs[] = {
	&sensor_dev_attr_sfp_enable2.dev_attr.attr,
	&sensor_dev_attr_broad_front_lct.dev_attr.attr,
	&sensor_dev_attr_broad_front_bmc.dev_attr.attr,
	&sensor_dev_attr_broad_front_cpu.dev_attr.attr,
	&sensor_dev_attr_broad_front_pwr.dev_attr.attr,
	&sensor_dev_attr_broad_front_fan.dev_attr.attr,
	&sensor_dev_attr_sfp_led2_yellow.dev_attr.attr,
	&sensor_dev_attr_mac_temp_input.dev_attr.attr,
	&sensor_dev_attr_cpld_version.dev_attr.attr,
	NULL
};

static const struct attribute_group cpld32_sysfs_group = {
	.attrs = cpld32_sysfs_attrs,
};

static const struct attribute_group cpld37_sysfs_group = {
	.attrs = cpld37_sysfs_attrs,
};

static const struct attribute_group cpld33_sysfs_group = {
	.attrs = cpld33_sysfs_attrs,
};

static const struct attribute_group cpld34_sysfs_group = {
	.attrs = cpld34_sysfs_attrs,
};

static const struct attribute_group  cpld36_sysfs_group = {
	.attrs = cpld36_sysfs_attrs,
};

static const struct attribute_group  cpld35_sysfs_group = {
	.attrs = cpld35_sysfs_attrs,
};

static struct attribute *cpld_hwmon_attrs[] = {
	&sensor_dev_attr_fan1_input.dev_attr.attr,
	&sensor_dev_attr_fan2_input.dev_attr.attr,
	&sensor_dev_attr_fan3_input.dev_attr.attr,
	&sensor_dev_attr_fan4_input.dev_attr.attr,
	NULL
};
ATTRIBUTE_GROUPS(cpld_hwmon);

struct cpld_attr_match_group {
	int bus_nr;          /* I2C BUS */
	unsigned short addr; /* slave addr*/
	const struct attribute_group   *attr_group_ptr;
	const struct attribute_group   *attr_hwmon_ptr;
};

static struct cpld_attr_match_group g_cpld_attr_match[] = {
	{0, 0x32, &cpld32_sysfs_group, NULL},
	{2, 0x37, &cpld37_sysfs_group, (struct attribute_group *)cpld_hwmon_groups},
	{2, 0x33, &cpld33_sysfs_group, NULL},
	{1, 0x34, &cpld34_sysfs_group, NULL},
	{1, 0x36, &cpld36_sysfs_group, NULL},
	{2, 0x35, &cpld35_sysfs_group, NULL},
};

static  const struct attribute_group *cpld_get_attr_group(struct i2c_client *client, int is_hwmon)
{
	int i;
	struct cpld_attr_match_group *group;

	for (i = 0; i < ARRAY_SIZE(g_cpld_attr_match); i++) {
		group = &g_cpld_attr_match[i];
		DBG_DEBUG("is_hwmon %d i %d client(nr:%d,addr:0x%x), group(nr:%d,addr:0x0%x).\n", is_hwmon,
			i, client->adapter->nr, client->addr, group->bus_nr, group->addr);
		if ((client->addr == group->addr) && (client->adapter->nr == group->bus_nr)) {
			DBG_DEBUG("is_hwmon %d i %d nr %d addr %d .\n", is_hwmon, i, client->adapter->nr, client->addr);
			return (is_hwmon) ? (group->attr_hwmon_ptr) : (group->attr_group_ptr);
		}
	}

	DBG_DEBUG("is_hwmon %d nr %d addr %d dismatch, return NULL.\n", is_hwmon, client->adapter->nr, client->addr);
	return NULL;
}

static int cpld_probe(struct i2c_client *client, const struct i2c_device_id *id)
{
    struct cpld_data *data;
    int status;
    const struct attribute_group *sysfs_group, *hwmon_group;

    status = -1;
    DBG_DEBUG("=========cpld_probe(addr:0x%x, nr:%d)===========\n", client->addr, client->adapter->nr);
    data = devm_kzalloc(&client->dev, sizeof(struct cpld_data), GFP_KERNEL);
    if (!data) {
        return -ENOMEM;
    }
    
    data->client = client;
    i2c_set_clientdata(client, data);
    mutex_init(&data->update_lock);

    sysfs_group = NULL;
    sysfs_group = cpld_get_attr_group(client, 0);
    if (sysfs_group) {
        status = sysfs_create_group(&client->dev.kobj, sysfs_group);
        DBG_DEBUG("=========(addr:0x%x, nr:%d) sysfs_create_group status %d===========\n", client->addr, client->adapter->nr, status);
        if (status != 0) {
            DBG_ERROR("sysfs_create_group status %d.\n", status);
            goto error; 
        }
    } else {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) no sysfs_create_group \n", client->addr, client->adapter->nr);
    }
    
    hwmon_group = NULL;
    hwmon_group = cpld_get_attr_group(client, 1);
    if (hwmon_group) {
        data->hwmon_dev = hwmon_device_register_with_groups(&client->dev, client->name, data, (const struct attribute_group **)hwmon_group);
        if (IS_ERR(data->hwmon_dev)) {
            sysfs_remove_group(&client->dev.kobj,  (const struct attribute_group *)sysfs_group);
            DBG_ERROR("hwmon_device_register_with_groups failed ret %ld.\n", PTR_ERR(data->hwmon_dev));
            return PTR_ERR(data->hwmon_dev);
        }
        DBG_DEBUG("=========(addr:0x%x, nr:%d) hwmon_device_register_with_groups success===========\n", client->addr, client->adapter->nr);
        if (status != 0) {
            DBG_ERROR("sysfs_create_group status %d.\n", status);
            goto error; 
        }
    } else {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) no hwmon_device_register_with_groups \n", client->addr, client->adapter->nr);
    }

error:
    return status;

}

static int cpld_remove(struct i2c_client *client)
{
    struct cpld_data *data = i2c_get_clientdata(client);
    const struct attribute_group *sysfs_group, *hwmon_group;
    
    DBG_DEBUG("=========cpld_remove(addr:0x%x, nr:%d)===========\n", client->addr, client->adapter->nr);

    sysfs_group = NULL;
    sysfs_group = cpld_get_attr_group(client, 0);
    if (sysfs_group) {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) do sysfs_remove_group \n", client->addr, client->adapter->nr);
        sysfs_remove_group(&client->dev.kobj, (const struct attribute_group *)sysfs_group);
    } else {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) no sysfs_remove_group \n", client->addr, client->adapter->nr);
    }
    
    hwmon_group = NULL;
    hwmon_group = cpld_get_attr_group(client, 1);
    if (hwmon_group) {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) do hwmon_device_unregister \n", client->addr, client->adapter->nr);
        hwmon_device_unregister(data->hwmon_dev);
    } else {
        DBG_DEBUG("=========(addr:0x%x, nr:%d) no hwmon_device_unregister \n", client->addr, client->adapter->nr);
    }   
    
    return 0;
}


static const struct i2c_device_id cpld_id[] = {
	{ "rg_cpld", 0 },
	{}
};

MODULE_DEVICE_TABLE(i2c, cpld_id);

static struct i2c_driver rg_cpld_driver = {
	.class    = I2C_CLASS_HWMON,
	.driver   = {
		.name = "rg_cpld",
	},
	.probe    = cpld_probe,
	.remove   = cpld_remove,
	.id_table = cpld_id,
};

module_i2c_driver(rg_cpld_driver);

MODULE_AUTHOR("support <support@ragile.com>");
MODULE_DESCRIPTION("ragile CPLD driver");
MODULE_LICENSE("GPL");
