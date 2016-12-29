# Command packets
import struct
import binascii

from hcipacket import HCIPacket, HCI_COMMAND_PACKET

class HCICommand:
    def __init__(self, params=b''):
        self.opcode = (self.OGF<<10)|self.OCF
        self.params = params
        self.completion = None

    def withCompletion(self, callback):
        self.completion = callback
        return self

    def getPacket(self):
        return HCIPacket(HCI_COMMAND_PACKET, struct.pack("<HB", self.opcode, len(self.params)) + self.params)

    def onResponse(self, payload):
        self.status = payload[0]
        if self.status == 0:
            self.parseResponse(payload)
        if self.completion:
            print("Calling completer for opcode 0x%04X (%s)" % (self.opcode, self.__class__))
            self.completion(self)

    def parseResponse(self, payload):
        if len(payload) > 1:
            print ("Cmd (opcode 0x%04X) ignored payload %s" % binascii.b2a_hex(payload))

    def error(self):
        if self.status==0:
            return None
        return "HCI Error code %d" % self.status

# Informational commands ---------------------

class ReadLocalVersion(HCICommand):
    OGF = 0x04
    OCF = 0x0001

    BLUETOOTH_V4_0 = 6 # from https://www.bluetooth.com/specifications/assigned-numbers/host-controller-interface
    def parseResponse(self, payload):
        (self.status, self.version, self.revision, self.lmp, self.manuf, self.lmp_sub) = (
            struct.unpack("<BBHBHH", payload) )

    def __str__(self):
        return ("Ver %d rev 0x%04X manuf=0x%04X" % (self.version, self.revision, self.manuf))

# HCI controller commands ----------

class HCIControllerCommand(HCICommand):
    OGF = 0x03

class SetEventMask(HCIControllerCommand):
    OCF = 0x0001

    def __init__(self, eventMask):
        HCIControllerCommand.__init__(self, struct.pack("<Q", eventMask))

class WriteLEHostSupported(HCIControllerCommand):
    OCF = 0x006D

    LE_DISABLE = 0x00
    LE_ENABLE = 0x01
    LE_SIMUL_DISABLE = 0x00
    LE_SIMUL_ENABLE = 0x01

    def __init__(self, leSupported, simulLeSupported):
        HCIControllerCommand.__init__(self, struct.pack("<BB", leSupported, simulLeSupported))

# LE controller commands ----------
 
class LEControllerCommand(HCICommand):
    OGF = 0x08

class LESetEventMask(LEControllerCommand):
    OCF = 0x0001

    def __init__(self, eventMask):
        LEControllerCommand.__init__(self, struct.pack("<Q", eventMask))

    # Response is just status

class LEReadBufferSize(LEControllerCommand):
    OCF = 0x0002

    # No cmd parameters

    def parseResponse(self, payload):
        (self.status, self.packetlength, self.maxpackets) = (
            struct.unpack("<BHB", payload) )

class LEReadLocalSupportedFeatures(LEControllerCommand):
    OCF = 0x0003

    def parseResponse(self, payload):
         (self.status, self.features) = struct.unpack("<BQ", payload)

class LESetAdvertisingParameters(LEControllerCommand):
    OCF = 0x0006

    # TODO: add symbolic values when necessary

    def __init__(self,
         interval_min = 0x0800,
         interval_max = 0x0800,
         adv_type = 0,
         own_addr_type = 0,
         direct_addr_type = 0,
         direct_addr = b'\x00\x00\x00\x00\x00\x00',
         adv_channel_map = 7,
         adv_filter_policy = 0):
        if len(direct_addr) != 6:
            raise ValueError("direct_addr must be 6 bytes")
        LEControllerCommand.__init__(self, struct.pack("<HHBBBsBB",
            (interval_min, interval_max, adv_type, own_addr_type, direct_addr_type,
               bytes(direct_addr), adv_channel_map, adv_filter_policy) ))

class LESetAdvertisingData(LEControllerCommand):
    OCF = 0x0008

    def __init__(self, advData):
        ld = len(advData)
        if ld > 31:
            raise ValueError("Advertising/Scan response data too long (%d > 31 bytes)" % ld)
        payload = bytes([ld]) + advData + bytes([0] * (31-ld))
        LEControllerCommand.__init__(self, payload)

class LESetScanResponseData(LEControllerCommand):
    OCF = 0x0009

    def __init__(self, advData):
        LESetAdvertisingData.__init__(self, advData)


class LESetAdvertiseEnable(LEControllerCommand):
    OCF = 0x000A

    DISABLE = 0x00
    ENABLE = 0x01

    def __init__(self, state):
        LEControllerCommand.__init__(self, struct.pack("<B", state))

class LESetScanParameters(LEControllerCommand):
    OCF = 0x000B

    # TODO: add symbolic values when necessary
    # BT 4.0 spec, 7.8.10

    def __init__(self,
         scan_type = 0,
         scan_interval = 0x0010,
         scan_window = 0x0010,
         own_addr_type = 0,
         scan_filter_policy = 0):
        LEControllerCommand.__init__(self, struct.pack("<BHHBB",
            (scan_type, scan_interval, scan_window, own_addr_type, scan_filter_policy) ))

class LESetScanEnable(LEControllerCommand):
    OCF = 0x000C

    DISABLE = 0x00
    ENABLE = 0x01

    def __init__(self, state, filter_duplicates=False):
        filt = 1 if filter_duplicates else 0
        LEControllerCommand.__init__(self, struct.pack("<BB", state, filt))

        

