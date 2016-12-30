import binascii
import struct

GAP_FLAGS = 0x01
GAP_UUID_16BIT_INCOMPLETE = 0x02
GAP_UUID_16BIT_COMPLETE = 0x03
GAP_UUID_128BIT_INCOMPLETE = 0x06
GAP_UUID_128BIT_COMPLETE = 0x07
GAP_NAME_INCOMPLETE = 0x08
GAP_NAME_COMPLETE = 0x09


class AdvertisingData:
    def __init__(self):
        self.data = b''

    def addItem(self, tag, value):
        newdata = self.data + struct.pack("<BB", 1+len(value), tag) + bytes(value)
        if len(newdata) <= 31:
            self.data = newdata
        else:
            print ("Oops - advertising data too long")

    
