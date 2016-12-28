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
        return HCIPacket(HCI_COMMAND_PACKET, struct.pack("<HH", self.opcode, len(self.params)) + self.params)

    def onResponse(self, payload):
        self.parseResponse(payload)
        if self.completion:
            self.completion(self)

    def parseResponse(self, payload):
        print ("Currently ignoring payload (%d bytes)" % len(payload))

class ReadLocalVersion(HCICommand):
    OGF = 0x04
    OCF = 0x0001

class LEControllerCommand(HCICommand):
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

