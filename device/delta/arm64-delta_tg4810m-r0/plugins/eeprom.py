#!/usr/bin/env python
try:
    import os
    from sonic_eeprom import eeprom_tlvinfo
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

class board(eeprom_tlvinfo.TlvInfoDecoder):

    def __init__(self, name, path, cpld_root, ro):
        self.eeprom_path = "/sys/class/i2c-adapter/i2c-0/0-0057/eeprom"
        if not os.path.exists(self.eeprom_path):
                os.system("echo 24c64 0x57 > /sys/class/i2c-adapter/i2c-0/new_device")
        super(board, self).__init__(self.eeprom_path, 0, '', True)
