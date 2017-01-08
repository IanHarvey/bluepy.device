import os
import binascii

script_path = os.path.join(os.path.abspath(os.path.dirname(__file__)))

short_uuid_suffix = "00001000800000805F9B34FB"
short_uuid_suffix_bin = binascii.a2b_hex(short_uuid_suffix)

class UUID:
    def __init__(self, val, commonName=None):
        '''We accept: 32-digit hex strings, with and without '-' characters,
           4 to 8 digit hex strings, and integers'''
        if isinstance(val, int):
            if (val < 0) or (val > 0xFFFFFFFF):
                raise ValueError(
                    "Short form UUIDs must be in range 0..0xFFFFFFFF")
            val = "%04X" % val
        elif isinstance(val, self.__class__):
            val = str(val)
        else:
            val = str(val)  # Do our best

        val = val.replace("-", "")
        if len(val) <= 8:  # Short form
            val = ("0" * (8 - len(val))) + val + short_uuid_suffix

        self.binVal = binascii.a2b_hex(val.encode('utf-8'))
        if len(self.binVal) != 16:
            raise ValueError(
                "UUID must be 16 bytes, got '%s' (len=%d)" % (val,
                                                              len(self.binVal)))
        self.commonName = commonName

    def __str__(self):
        s = binascii.b2a_hex(self.binVal).decode('utf-8')
        return "-".join([s[0:8], s[8:12], s[12:16], s[16:20], s[20:32]])

    def __eq__(self, other):
        return self.binVal == UUID(other).binVal

    def __cmp__(self, other):
        return cmp(self.binVal, UUID(other).binVal)

    def __hash__(self):
        return hash(self.binVal)

    def getCommonName(self):
        s = AssignedNumbers.getCommonName(self)
        if s:
            return s
        s = str(self)
        if s.endswith("-0000-1000-8000-00805f9b34fb"):
            s = s[0:8]
            if s.startswith("0000"):
                s = s[4:]
        return s


def capitaliseName(descr):
    words = descr.split(" ")
    capWords =  [ words[0].lower() ]
    capWords += [ w[0:1].upper() + w[1:].lower() for w in words[1:] ]
    return "".join(capWords)

class _UUIDNameMap:
    # Constructor sets self.currentTimeService, self.txPower, and so on
    # from names.
    def __init__(self, idList):
        self.idMap = {}

        for uuid in idList:
            attrName = capitaliseName(uuid.commonName)
            vars(self) [attrName] = uuid
            self.idMap[uuid] = uuid

    def getCommonName(self, uuid):
        if uuid in self.idMap:
            return self.idMap[uuid].commonName
        return None

def get_json_uuid():
    import json
    with open(os.path.join(script_path, 'uuids.json'),"rb") as fp:
        uuid_data = json.loads(fp.read().decode("utf-8"))
    for k in ['service_UUIDs', 'characteristic_UUIDs', 'descriptor_UUIDs' ]:
        for number,cname,name in uuid_data[k]:
            yield UUID(number, cname)
            yield UUID(number, name)

AssignedNumbers = _UUIDNameMap( list(get_json_uuid() ))


