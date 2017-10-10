# GATT commands - issued by Central

# WORK IN PROGRESS - not suitable for use yet

import struct
import binascii
import uuid


# Command dispatch. Core 4.0 spec Vol 3 Part F, 3.4.2-7 --- 
class GATTCommand:
    def __init__(self, data_):
        self.data = data_

class ExchangeMTU(GATTCommand):
    # Vol 3 / F / 3.4.2
    def __init__(self, mtu): # Defaults?
        GATTCommand.__init__(self, struct.pack("<BH", 0x02, mtu) )
        # result is struct.pack("<BH", 0x03, self.server.mtu)

class FindInformation(GATTCommand):
    # Vol 3 / F / 3.4.3.1
    def __init__(self, startHnd, endHnd):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x04, startHnd, endHnd))
        # result is struct.pack("<BB", 0x05, fmt) + rp.recdata

class FindByTypeValue(GATTCommand):
    # Vol 3 / F / 3.4.3.3
    def __init__(self, startHnd, endHnd):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x06, startHnd, endHnd))
        # result is struct.pack("<B", 0x07) + rp.recdata

class ReadByType(GATTCommand):
    # Vol 3 / F / 3.4.4.1
    def __init__(self, startHnd, endHnd):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x08, startHnd, endHnd))
        # result is struct.pack("<BB", 0x09, rp.reclen) + rp.recdata

class Read(GATTCommand):
     # Vol 3 / F / 3.4.4.3
    def __init__(self, handle):
        GATTCommand.__init__(self, struct.pack("<BH", 0x0A, handle))
        # result is struct.pack("<B", 0x0B) + attr.getValue()

class ReadBlob(GATTCommand):
    # Vol 3 / F / 3.4.4.5
    def __init__(self, handle, offset):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x0C, handle, offset))
        # result is struct.pack("<B", 0x0D) + cdata

class ReadMultiple(GATTCommand):
    # Vol 3 / F / 3.4.4.7
    def __init__(self, handleList):
        l = len(handleList)
        strL = "%d" % l
        GATTCommand.__init__(self, struct.pack("<BH"+strL+"H", 0x0E, l, *handleList) )
        # result is struct.pack("<B", 0x0F) + cdata


class ReadByGroupType(GATTCommand):
    # Vol 3 / F / 3.4.4.9
    def __init__(self, startHnd, endHnd):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x10, startHnd, endHnd))
    # result is struct.pack("<BB", 0x11, rp.reclen) + rp.recdata


class WriteRequest(GATTCommand):
    # Vol 3 / F / 3.4.5.1
    def __init__(self, handle, data):
        GATTCommand.__init__(self, struct.pack("<BH", 0x12, handle) + bytes(data))
        # result is struct.pack("<B", 0x13)

class WriteCommand(GATTCommand):
    def __init__(self, handle, value):
        GATTCommand.__init__(self, struct.pack("<BH", 0x52) + bytes(value))
        # No return

class PrepareWriteRequest(GATTCommand):
    def __init__(self, handle, offset, value):
        GATTCommand.__init__(self, struct.pack("<BHH", 0x16, handle, offset) + bytes(value))
        # result is struct.pack("<BHH", 0x17, handle, offset) + value

class ExecuteWriteRequest(GATTCommand):
    def __init__(self, flags):
        GATTCommand.__init__(self, struct.pack("<BB", 0x18, flags))
        # result is struct.pack("<B", 0x19)


r = ReadMultiple([1,4,5,6])
print( r.data )
