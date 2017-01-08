import struct
import binascii
import uuid


CID_GATT = 0x04

# Core 4.0 Spec, Vol 3 Part G, 3.4

UUID_PRIMARY_SERVICE     = 0x2800
UUID_SECONDARY_SERVICE   = 0x2801
UUID_INCLUDE_DEFINITION  = 0x2802
UUID_CHARACTERISTIC_DECL = 0x2803

UUID_CHAR_XTD_PROPERTIES = 0x2900
UUID_CHAR_USER_DESC      = 0x2901
UUID_CHAR_CLIENT_CONFIG  = 0x2902
UUID_CHAR_SERVER_CONFIG  = 0x2903
UUID_CHAR_FORMAT_DESC    = 0x2904
UUID_CHAR_AGG_FORMAT_DESC= 0x2905

# TODO: move to uuid.py?
def getShortForm(uid):
    if isinstance(uid, uuid.UUID):
       uid = uid.binVal
    else:
       uid = bytes(uid)
    if uid[0] == 0 and uid[1] == 0 and uid[4:16] == uuid.short_uuid_suffix_bin:
       return uid[2:4]
    return uid

# Base attribute class, usable for read-only attributes
class Attribute:
    def __init__(self, att_type, value=None):
        self.handle = None
        self.typeUUID = uuid.UUID(att_type)
        self.value = value

    def setHandle(self, hnd):
        self.handle = hnd

    def getValue(self):
        return self.value

    def isWriteable(self):
        return False

    def setValue(self, value):
        if self.value is not None:
            raise ValueError("Can only set attribute value once")
        self.value = value
        
    def __str__(self):
        if self.value is None:
            valstr = "<unset>"
        else:
            valstr = binascii.b2a_hex(self.value).decode("ascii")
        return ("Attr hnd=0x%04X UUID=%s val=%s" % (self.handle, self.typeUUID.getCommonName(),
                   valstr ) )

# Characteristics --------------------

# Core 4.0 Spec, Vol 3 Part G, 3.1

PROPS_BROADCAST  = 0x01
PROPS_READ       = 0x02
PROPS_WRITE_NOACK= 0x04
PROPS_WRITE      = 0x08
PROPS_NOTIFY     = 0x10
PROPS_INDICATE   = 0x20
PROPS_AUTH_WRITE = 0x40
PROPS_EXTENDED   = 0x80

class CharacteristicBase:
    def __init__(self):
        self.charDecl = Attribute(UUID_CHARACTERISTIC_DECL)
        self.value = None
        self.descriptors = []
        self.properties = PROPS_READ

    def withValueAttrib(self, valueAttr): 
        self.value = valueAttr
        return self

    def withDescriptor(self, desc):
        self.descriptors.append(desc)
        return self

    def withProperties(self, properties):
        self.properties = properties
        
    # TODO: create convenience wrappers for various descriptors

    def getAttributeList(self):
        # Called after all construction is complete
        assert self.value is not None
        return [ self.charDecl, self.value ] + self.descriptors
       
    def getEndHandle(self):
        if len(self.descriptors) > 0:
            return self.descriptors[-1].handle
        return self.value.handle
        
    def configure(self):
        self.charDecl.setValue ( struct.pack("<BH", self.properties, self.value.handle) +
                                   getShortForm(self.value.typeUUID) )

class ReadOnlyCharacteristic(CharacteristicBase):
    def __init__(self, charUUID, value):
        valAttr = Attribute(charUUID, value)
        CharacteristicBase.__init__(self)
        self.withValueAttrib(valAttr)

class Service():
    def __init__(self):
        self.svcDefn = None
        self.includes = []  # Service objects
        self.includeAttrs = [] # Descriptors for included services
        self.characteristics = [] # Characteristic objects

    def withPrimaryUUID(self, uid):
        self.UUID = uid
        self.svcDefn = Attribute(UUID_PRIMARY_SERVICE, getShortForm(uid))
        return self

    def withSecondaryUUID(self, uid):
        self.UUID = uid
        self.svcDefn = Attribute(UUID_SECONDARY_SERVICE, getShortForm(uid))
        return self

    def withIncludedService(self, svc):
        self.includes.append(svc)
        # Add placeholder attribute, will set value during configure()
        self.includeAttrs.append(Attribute(UUID_INCLUDE_DEFINITION))
        return self
       
    def withCharacteristic(self, ch):
        self.characteristics.append(ch)
        return self

    def withCharacteristics(self, chlist):
        self.characteristics += chlist
        return self

    def getAttributesList(self):
        alist = [self.svcDefn] + self.includeAttrs
        for ch in self.characteristics:
            alist += ch.getAttributeList()
        return alist

    def getHandleRange(self):
        # Returns first and last (i.e. End Group Handle) handles for this
        # service definition
        return ( self.svcDefn.handle, self.characteristics[-1].getEndHandle() )

    def configure(self):
        # All attributes of all services have their handles set at this point
        
        # Set values for included services
        i=0
        for isvc in self.includes:
            first, last = isvc.getHandleRange()
            uidfield = getShortForm(isvc.UUID)
            if len(uidfield) != 2:
                uidfield = b''
            print (i, self.includeAttrs[i])
            self.includeAttrs[i].setValue( struct.pack("<HH", first, last) + uidfield )
            i += 1
            
        for ch in self.characteristics:
            ch.configure()
       
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

    def _configureServices(self):
        hnd = 0x0001
        # Set handles
        for sv in self.services:
            for attr in sv.getAttributesList():
                attr.setHandle(hnd)
                self.handles[hnd] = attr
                hnd += 1
        # Update data now handles are set
        for sv in self.services:
            sv.configure()
                
    def withServices(self, serviceList):
        self.services = serviceList
        self._configureServices()
        return self

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
    ch2 = ReadOnlyCharacteristic(uuid.AssignedNumbers.deviceName, b'My device')
    sv2 = Service().withSecondaryUUID(uuid.UUID(0x3435)).withCharacteristic(ch2)
    
    ch = ReadOnlyCharacteristic(uuid.AssignedNumbers.deviceName, b'My device')
    sv = ( Service().withPrimaryUUID(uuid.AssignedNumbers.genericAccess)
             .withCharacteristic(ch)
             .withIncludedService(sv2)
         )

    gs=GattServer().withServices([sv, sv2])
    
    def show(dd):
        dks = list(dd.keys())
        dks.sort()
        for k in dks:
            print ("0x%04X -> %s" % (k, dd[k]))
            
    print ("Commands")
    show( gs.cmdDispatch )
    print ("Handles")
    show( gs.handles )

