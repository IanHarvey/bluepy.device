import struct
import binascii

# Vol 4 part 4.5
HCI_COMMAND_PACKET = 0x01
HCI_ACL_DATA_PACKET = 0x02
HCI_EVENT_PACKET = 0x04

class HCIPacket:
    def __init__(self, packetType):
        self.packetType = packetType
        self.payload = None

    def __str__(self):
        return "Type=%02X Payload=%s" % (self.packetType, binascii.b2a_hex(self.payload))

class HCICommandPacket(HCIPacket):
    def __init__(self, params=b''):
        HCIPacket.__init__(self,HCI_COMMAND_PACKET)
        self.payload = struct.pack("<HH", (self.OGF<<10)|self.OCF, len(params)) + params

class LEControllerCommand(HCICommandPacket):
    OGF = 0x08


class LESetEventMask(LEControllerCommand):
    OCF = 0x0001

    EVT_MASK_CONN_COMPLETE        = 0x0000000000000001
    EVT_MASK_ADVERTISING_REPORT   = 0x0000000000000002
    EVT_MASK_CONN_UPDATE_COMPLETE = 0x0000000000000004
    EVT_MASK_REMOTE_FEAT_COMPLETE = 0x0000000000000008
    EVT_MASK_LONGTERM_KEY_REQUEST = 0x0000000000000010
    EVT_MASK_DEFAULT              = 0x000000000000001F

    def __init__(self, eventMask):
        LEControllerCommand.__init__(self, struct.pack("<Q", eventMask))

class LEReadBufferSize(LEControllerCommand):
    OCF = 0x0002

class LEReadLocalSupportedFeatures(LEControllerCommand):
    OCF = 0x0003

class LESetScanResponseData(LEControllerCommand):
    OCF = 0x0009

class LESetAdvertiseEnable(LEControllerCommand):
    OCF = 0x000A

class LESetScanParameters(LEControllerCommand):
    OCF = 0x000B

if __name__ == '__main__':
    print( LESetEventMask(LESetEventMask.EVT_MASK_DEFAULT) )
    print( LEReadBufferSize() )

