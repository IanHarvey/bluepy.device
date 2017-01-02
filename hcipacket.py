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

    def getAclChannel(self):
        if self.packetType == HCI_ACL_DATA_PACKET:
            return (struct.unpack("<H", self.payload[0:2])[0] & 0xFFF)
        else:
            return None
       
    def toBytes(self):
        return bytes([self.packetType]) + self.payload
       
# Packet boundary flags
FRAG_FLAGS = 0x3000
FRAG_FIRST = 0x2000
FRAG_NEXT  = 0x1000
FRAG_FIRST_HOST = 0x0000

class ACLConnection:
    def __init__(self, sock, handle):
        self.sock = sock
        self.handle = handle
        self.channelFns = {} # Maps channel ID to callable
        self.fragBuf = None
        self.fragCID = 0
        self.fragPktLen = 0
        self.txMtu = 9999

    def withChannel(self, cid, callback):
        self.channelFns[cid] = callback
        return self

    # Deals with reassembly of fragmented receive packets
    def onReceivedData(self, data):
        (hnd_flags, fraglen) = struct.unpack("<HH", data[0:4])
        if fraglen+4 != len(data):
            print ("Invalid ACL length %d" % fraglen) 
            return
        if (hnd_flags & FRAG_FLAGS) == FRAG_FIRST:
            (pktlen,cid) = struct.unpack("<HH", data[4:8])
            print ("First frag, cid=%02X pktlen=%04X" % (cid, pktlen))
            if pktlen+4 == fraglen:
                return self.onPacketComplete(cid, data[8:])
            else:
                self.fragBuf = data[8:]
                self.fragCID = cid
                self.fragPktLen = pktlen
                print ("Have %d/%d, buffering" % (fraglen-4,pktlen)) 
                return
        elif (hnd_flags & FRAG_FLAGS) == FRAG_NEXT:
            self.fragBuf += data[4:]
            print ("Buffer length now %d/%d" % (len(self.fragBuf), self.fragPktLen))
            if len(self.fragBuf) < self.fragPktLen:
                return
            return self.onPacketComplete(self.fragCID, self.fragBuf[0:self.fragPktLen])
            
        print ("Unhandled ACL receive data hnd_flags=0x%04X" % hnd_flags)

    def onPacketComplete(self, cid, data):
        if cid in self.channelFns:
            print ("Dispatch %d bytes to CID %d" % (len(data), cid))
            return self.channelFns[cid](self, cid, data)
        else:
            print ("Dropping data with CID=%d" % cid)

    def send(self, cid, data):
        # FIXME: what is MTU here?
        dlen = len(data)
        if dlen <= self.txMtu - 8:
            payload = struct.pack("<HHHH", FRAG_FIRST_HOST | self.handle,
                dlen+4, dlen, cid) + data
            self.sock.queuePacket(HCIPacket(HCI_ACL_DATA_PACKET, payload))
        else:
            pdu = struct.pack("<HH", dlen, cid) + data
            pos = 0
            remain = len(pdu)
            flags = FRAG_FIRST_HOST | self.handle
            while remain > 0:
                n = min(remain, self.txMtu-4)
                payload = struct.pack("<HH", flags, n) + data[pos : pos+n]
                self.sock.queuePacket(HCIPacket(HCI_ACL_DATA_PACKET, payload))
                flags = FRAG_NEXT | self.handle
                pos += n
                remain -= n

    def onDisconnect(self, reason):
        print ("Handle 0x%04X disconnecting, reason 0x%02X" % (self.handle, reason))


