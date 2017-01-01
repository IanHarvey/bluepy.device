import struct
import binascii

CID_GATT = 0x04

class GattObject:
    def __init__(self, handle):
        self.handle = handle


# Error codes. Core 4.0 spec Vol 3 Part F, 3.4.1
E_INVALID_HANDLE      = 0x01
E_READ_NOT_PERMITTED  = 0x02
E_WRITE_NOT_PERMITTED = 0x03
E_INVALID_PDU         = 0x04
E_INSUFFICIENT_AUTHN  = 0x05
E_REQ_NOT_SUPPORTED   = 0x06
E_INVALID_OFFSET      = 0x07
E_INSUFFICIENT_AUTHZ  = 0x08
E_PREPARE_Q_FULL      = 0x09
E_ATTR_NOT_FOUND      = 0x0A
E_ATTR_NOT_LONG       = 0x0B
E_INSUFF_ENC_KEY_SZ   = 0x0C
E_INVALID_ATTRIB_LEN  = 0x0D
E_UNLIKELY_ERROR      = 0x0E
E_INSUFF_ENCRYPTION   = 0x0F
E_UNSUPPORTED_GROUP_T = 0x10
E_INSUFF_RESOURCES    = 0x11


class Command:
    opcode = None

    def __init__(self, server, opc=None):
        self.server = server
        if opc is not None:
            self.opcode = opc

    def execute(self, params):
        return self.error(E_REQ_NOT_SUPPORTED)

    def error(self, code, handle=0x0000):
        return struct.pack("<BBHB", 0x01, self.opcode, handle, code)

class ExchangeMTU(Command):
    opcode = 0x02

class FindInformation(Command):
    opcode = 0x04

class FindByTypeValue(Command):
    opcode = 0x06

class ReadByType(Command):
    opcode = 0x08

class Read(Command):
    opcode = 0x0A

class ReadBlob(Command):
    opcode = 0x0C

class ReadMultiple(Command):
    opcode = 0x0E

class ReadByGroupType(Command):
    opcode = 0x10

class Write(Command):
    opcode = 0x12


class GattServer:
    def __init__(self):
        self.services = []
        self.handles = {}
        self.cmdDispatch = {}
        for cmdclass in [
           ExchangeMTU, 
           FindInformation, FindByTypeValue,
           ReadByType, Read, ReadBlob, ReadMultiple, ReadByGroupType,
           Write, #...
           ]:
            cmd = cmdclass(self)
            self.cmdDispatch[cmd.opcode] = cmd

    def onMessageReceived(self, handle, data):
        # Use as channel callback for hcipacket.ACLConnection
        opcode = data[0]
        if opcode in self.cmdDispatch:
            print ("Dispatch opcode %s", self.cmdDispatch[opcode])
            resp = self.cmdDispatch[opcode].execute(data)
        else:
            print ("Unknown opcode 0x%02X" % opcode)
            resp = Command(self, opcode).error(E_REQ_NOT_SUPPORTED)
        print ("Resp is %s" % resp)

if __name__ == '__main__':
    r=GattServer()
    print( r.cmdDispatch )

