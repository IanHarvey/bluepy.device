import struct
import binascii

# Vol 4 part 4.5
HCI_COMMAND_PACKET = 0x01
HCI_ACL_DATA_PACKET = 0x02
HCI_EVENT_PACKET = 0x04

class HCIPacket:
    @staticmethod
    def fromBytes(buf):
        return HCIPacket(buf[0], buf[1:])

    def __init__(self, packetType, payload):
        self.packetType = packetType
        self.payload = payload

    def __str__(self):
        return "Type=%02X Payload=%s" % (self.packetType, binascii.b2a_hex(self.payload))

    def toBytes(self):
        return bytes([self.packetType]) + self.payload
       
