import struct
import binascii
import uuid


CID_GATT = 0x04

UUID_PRIMARY_SERVICE     = 0x2800
UUID_SECONDARY_SERVICE   = 0x2801
UUID_INCLUDE_DEFINITION  = 0x2802
UUID_CHARACTERISTIC_DECL = 0x2803

# TODO: move to uuid.py?
def getShortForm(uid):
    if isinstance(uid, uuid.UUID):
       uid = uid.binVal
    else:
       uid = bytes(uid)
    if uid[0] == 0 and uid[1] == 0 and uid[4:16] == uuid.short_uuid_suffix_bin:
       return uid[2:4]
    return uid

# Base attribute class
class Attribute:
    def __init__(self, att_type, value):
        self.handle = None
        self.typeUUID = UUID(att_type)
        self.value = value

    def setHandle(self, hnd):
        self.handle = hnd

    def getValue(self):
        return self.value

    def isWriteable(self):
        return False

    def setValue(self):
        pass


class CharacteristicBase:
    def __init__(self):
       self.charDesc = None
       self.value = None
       self.descriptors = []

    def withValueAttrib(self, valAttr): 
       self.value = valAttr
       self.charDesc = Attribute(UUID_CHARACTERISTIC_DECL, getShortForm(valAttr.typeUUID))
       return self

    def withDescriptor(self, desc):
       self.descriptors.append(desc)
       return self

    # TODO: create convenience wrappers for various descriptors

    def getAttributeList(self):
       # Called after all construction is complete
       assert self.value is not None
       return [ self.charDesc, self.value ] + self.descriptors

class ReadOnlyCharacteristic(CharacteristicBase):
    def __init__(self, charUUID, value):
        valAttr = Attribute(charUUID, value)
        return CharacteristicBase.__init__(self).withValueAttrib(valAttr)

class Service():
    def __init__(self):
       self.svcDesc = None
       self.includes = []  # Attribute objects
       self.characteristics = [] # Characteristic objects

    def withPrimaryUUID(self, uid):
       self.svcUUID = uid
       self.svcDesc = Attribute(UUID_PRIMARY_SERVICE, getShortForm(uid))
       return self

    def withSecondaryUUID(self, uid):
       self.svcUUID = uid
       self.svcDesc = Attribute(UUID_SECONDARY_SERVICE, getShortForm(uid))
       return self

    def withIncludedService(self, svc):
       attr = Attribute(UUID_INCLUDE_DEFINITION, getShortForm(svc.svcUUID))
       # FIXME - is this correct?
       self.includes.append(attr)
       return self
       
    def withCharacteristic(self, ch):
       self.characteristics.append(ch)
       return self

    def getAttributesList(self):
       alist = [self.svcDesc] + self.includes
       for ch in self.characteristics:
           alist.append(ch.getAttributeList)
       return alist


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

# Command dispatch 
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

    def execute(self, params):
        theirMTU = struct.unpack("<BH", params)[1]
        self.server.mtu = min(theirMTU, self.server.mtu)
        print ("MTU now %d" % self.server.mtu)
        return struct.pack("<BH", 0x03, self.server.mtu)

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
        self.mtu = 9999
        for cmdclass in [
           ExchangeMTU, 
           FindInformation, FindByTypeValue,
           ReadByType, Read, ReadBlob, ReadMultiple, ReadByGroupType,
           Write, #...
           ]:
            cmd = cmdclass(self)
            self.cmdDispatch[cmd.opcode] = cmd

    def onMessageReceived(self, aclconn, cid, data):
        # Use as channel callback for hcipacket.ACLConnection
        opcode = data[0]
        if opcode in self.cmdDispatch:
            print ("Dispatch opcode %s" % self.cmdDispatch[opcode])
            resp = self.cmdDispatch[opcode].execute(data)
        else:
            print ("Unknown opcode 0x%02X" % opcode)
            resp = Command(self, opcode).error(E_REQ_NOT_SUPPORTED)
        print ("Resp is %s" % resp)
        aclconn.send(cid, resp)

if __name__ == '__main__':
    r=GattServer()
    print ( r.cmdDispatch )
    print ( getShortForm(uuid.AssignedNumbers.weightMeasurement) )
    print ( getShortForm(uuid.UUID("28381892")) )
    print ( getShortForm(uuid.UUID(0x2903)) )


