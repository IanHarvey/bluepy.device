import binascii
import struct

# Generic Access Profile
# BT Spec V4.0, Volume 3, Part C, Section 18

GAP_FLAGS = 0x01
GAP_UUID_16BIT_INCOMPLETE = 0x02
GAP_UUID_16BIT_COMPLETE = 0x03
GAP_UUID_128BIT_INCOMPLETE = 0x06
GAP_UUID_128BIT_COMPLETE = 0x07
GAP_NAME_INCOMPLETE = 0x08
GAP_NAME_COMPLETE = 0x09
GAP_TX_POWER = 0x0A

class AdvertisingData:
    def __init__(self, withData=b''):
        self.data = bytes(withData)

    def addItem(self, tag, value):
        newdata = self.data + struct.pack("<BB", 1+len(value), tag) + bytes(value)
        if len(newdata) <= 31:
            self.data = newdata
        else:
            raise IndexError("Supplied advertising data too long (%d bytes total)", len(newdata))
        return self

    def __iter__(self):
        '''Use: for (tag,value) in obj:'''
        ofs = 0
        maxlen = len(self.data)
        while ofs < maxlen:
            if maxlen - ofs < 2:
                raise IndexError("Advertising data too short")
            (ll, tag) = struct.unpack("<BB", self.data[ofs:ofs+2])
            if ll==0 or ofs+1+ll > maxlen:
                raise IndexError("Bad length byte 0x%02X in advertising data" % ll)
            yield (tag, self.data[ofs+2:ofs+1+ll])
            ofs = ofs + 1 + ll
            

if __name__ == '__main__':
    a = AdvertisingData().addItem(GAP_FLAGS, b'11').addItem(GAP_NAME_COMPLETE, b'ThisIsMyName')
    print( binascii.b2a_hex(a.data) )
    for x in a:
        print (repr(x))
