#!/usr/bin/env python
# sfputil.py
# Platform-specific SFP functionality for SONiC
try:
    import os
    import time
    import re
    import sys
    import glob
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

if sys.version_info[0] < 3:
    import commands as cmd
else:
    import subprocess as cmd

smbus_present = 1
try:
    import smbus
except ImportError, e:
    smbus_present = 0

class SfpUtil(SfpUtilBase):
    """Platform specific sfputil class"""
    _port_start = 1
    _port_end = 48
    ports_in_block = 48
    _port_to_eeprom_mapping = {}
    port_to_i2c_mapping = {
    }
    #_qsfp_ports = range(_port_start, ports_in_block + 1)
    _qsfp_ports = {}
    _changed_ports = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    def __init__(self):

        # SFP Tx Enable 
        if smbus_present == 0 :
            os.system("i2cset -y  2 0x41 0x31 0x00")
            os.system("i2cset -y  2 0x41 0x32 0x00")
            os.system("i2cset -y  2 0x41 0x33 0x00")
            os.system("i2cset -y  2 0x41 0x34 0x00")
            os.system("i2cset -y  2 0x41 0x35 0x00")
            os.system("i2cset -y  2 0x41 0x36 0x00")
        else :
            bus = smbus.SMBus(2)
            DEVICE_ADDRESS = 0x41
            DEVICEREG = 0x31
            OPTIC_E = 0x00
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)
            DEVICEREG = 0x32
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)
            DEVICEREG = 0x33
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)
            DEVICEREG = 0x34
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)
            DEVICEREG = 0x35
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)
            DEVICEREG = 0x36
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, OPTIC_E)

        # Mux Ordering
        mux_dev = sorted(glob.glob("/sys/class/i2c-adapter/i2c-1/i2c-*[0-9]*"))
        # Enable optoe2 Driver
        eeprom_path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/eeprom"
        bus_path = "/sys/class/i2c-adapter/i2c-{0}/"
        y = 0
        for x in range(self.port_start, self.port_end + 1):
            mux_dev_num = mux_dev[y]
            self.port_to_i2c_mapping[x] = mux_dev_num.split('-')[-1]
            physical_port = int(self.port_to_i2c_mapping[x]) - 2 
            y = y + 1
            port_eeprom_path = eeprom_path.format(self.port_to_i2c_mapping[x])
            if not os.path.exists(port_eeprom_path):
                bus_dev_path = bus_path.format(self.port_to_i2c_mapping[x])
                #print(bus_dev_path)
                os.system("echo optoe2 0x50 > " + bus_dev_path + "/new_device")
            self.port_to_eeprom_mapping[physical_port] = port_eeprom_path
            self._port_to_eeprom_mapping[physical_port] = port_eeprom_path
            #print self._port_to_eeprom_mapping[physical_port]
        SfpUtilBase.__init__(self)

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False
        path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/sfp_port_reset"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False
        #toggle reset
        reg_file.seek(0)
        reg_file.write('1')
        time.sleep(1)
        reg_file.seek(0)
        reg_file.write('0')
        reg_file.close()
        return True

    def set_low_power_mode(self, port_nuM, lpmode):
        raise NotImplementedError

    def get_low_power_mode(self, port_num):
        raise NotImplementedError

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False
        if port_num >=1 and port_num <=8:
            prt = port_num -1
            DEVICE_REG = 0x3a
        if port_num >=9 and port_num <=16:
            prt = port_num % 9
            DEVICE_REG = 0x3b
        if port_num >=17 and port_num <=24:
            prt = port_num % 17
            DEVICE_REG = 0x3c
        if port_num >=25 and port_num <=32:
            prt = port_num % 25
            DEVICE_REG = 0x3d
        if port_num >=33 and port_num <=40:
            prt = port_num % 33
            DEVICE_REG = 0x3e
        if port_num >=41 and port_num <=48:
            prt = port_num % 41
            DEVICE_REG = 0x3f

        pos = [1,2,4,8,16,32,64,128]
        bit_pos = pos[prt]
        if smbus_present == 0:
	     #Read PSU presence register
             cmdstatus, sfpstatus = cmd.getstatusoutput("i2cget -y 2 0x41 "+ hex(DEVICE_REG) + " " ) #Verify CPLD register logic
             sfpstatus = int(sfpstatus, 16)
        else :
             bus = smbus.SMBus(2)
             DEVICE_ADDRESS = 0x41
             sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        sfpstatus = sfpstatus&(bit_pos)
        #print "checking presence"
        #print bit_pos
        #print sfpstatus
        #print port_num
        if sfpstatus == 0:
            #print "sfp found"
            return True
        return False
        
    def read_porttab_mappings(self, porttabfile):
        logical = []
        logical_to_physical = {}
        physical_to_logical = {}
        last_fp_port_index = 0
        last_portname = ""
        first = 1
        port_pos_in_file = 0
        parse_fmt_port_config_ini = False

        try:
            f = open(porttabfile)
        except:
            raise

        parse_fmt_port_config_ini = (os.path.basename(porttabfile) == "port_config.ini")
        # Read the porttab file and generate dicts
        # with mapping for future reference.
        #
        # TODO: Refactor this to use the portconfig.py module that now
        # exists as part of the sonic-config-engine package.
        title = []
        for line in f:
            line.strip()
            if re.search("^#", line) is not None:
                # The current format is: # name lanes alias index speed
                # Where the ordering of the columns can vary
                title = line.split()[1:]
                continue

            # Parsing logic for 'port_config.ini' file
            if (parse_fmt_port_config_ini):
                portname = line.split()[0]

                if "index" in title:
                    fp_port_index = int(line.split()[title.index("index")])
                # Leave the old code for backward compatibility
                elif len(line.split()) >= 4:
                    fp_port_index = int(line.split()[3])
                else:
                    fp_port_index = portname.split("Ethernet").pop()
                    fp_port_index = int(fp_port_index.split("s").pop(0))+1
                    #print(fp_port_index)
            else:  # Parsing logic for older 'portmap.ini' file
                fp_port_index = portname.split("Ethernet").pop()
                fp_port_index = int(fp_port_index.split("s").pop(0))+1

            if ((len(self.sfp_ports) > 0) and (fp_port_index not in self.sfp_ports)):
                continue

            if first == 1:
                # Initialize last_[physical|logical]_port
                # to the first valid port
                last_fp_port_index = fp_port_index
                last_portname = portname
                first = 0

            logical.append(portname)

            logical_to_physical[portname] = [fp_port_index]
            if physical_to_logical.get(fp_port_index) is None:
                physical_to_logical[fp_port_index] = [portname]
            else:
                physical_to_logical[fp_port_index].append(
                    portname)

            if (fp_port_index - last_fp_port_index) > 1:
                # last port was a gang port
                for p in range(last_fp_port_index+1, fp_port_index):
                    logical_to_physical[last_portname].append(p)
                    if physical_to_logical.get(p) is None:
                        physical_to_logical[p] = [last_portname]
                    else:
                        physical_to_logical[p].append(last_portname)

            last_fp_port_index = fp_port_index
            last_portname = portname

            port_pos_in_file += 1

        self.logical = logical
        self.logical_to_physical = logical_to_physical
        self.physical_to_logical = physical_to_logical
        #print(self.logical_to_physical)


    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end

    @property
    def qsfp_ports(self):
        return self._qsfp_ports

    @property
    def port_to_eeprom_mapping(self):
         return self._port_to_eeprom_mapping

    def get_transceiver_change_event(self, timeout):
        port_dict = {}

        if timeout == 0:
            cd_ms = sys.maxint
        else:
            cd_ms = timeout
        changed_port = 0
        #poll per second
        while cd_ms > 0:
           for port_num in range(1,48):
              sfpstatus = self.get_presence(port_num)
              if sfpstatus==0 :
                 port_dict[str(port_num)]= '1'
                 if self._changed_ports[port_num] == 0:
                     changed_port = 1
                     self._changed_ports[port_num] = 1
              else :
                 port_dict[str(port_num)] = '0'
                 if self._changed_ports[port_num] == 1:
                     changed_port = 1
                     self._changed_ports[port_num] = 0
           if changed_port != 0:
               break
           time.sleep(1)
           cd_ms = cd_ms - 1000

        if changed_port:
            return True, port_dict
        else:
            return True, {}

