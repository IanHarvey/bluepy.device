import struct
import binascii
import gap

# HCI Events
# Spec V4.0, Vol 2, sec 7.7

E_DISCONN_COMPLETE = 0x05
E_ENCRYPT_CHANGE = 0x08
E_CMD_RESPONSE = 0x0E
E_CMD_STATUS = 0x0F
E_LE_META_EVENT = 0x3E

# LE Meta-event subcodes
# Vol 2, 7.7.65

E_LE_CONN_COMPLETE = 0x01
E_LE_ADVERTISING_REPORT = 0x02
E_LE_CONN_UPDATE_COMPLETE = 0x03

def eventMask(evtList):
    w=0
    for e in evtList:
        assert(e > 0)
        w |= (1 << (e-1))
    return w

DEFAULT_EVENT_MASK = eventMask([E_DISCONN_COMPLETE, E_ENCRYPT_CHANGE, E_CMD_RESPONSE, E_CMD_STATUS, E_LE_META_EVENT])

DEFAULT_LE_EVENT_MASK = eventMask([E_LE_CONN_COMPLETE, E_LE_CONN_UPDATE_COMPLETE])

class EventHandler:
    # This is basically a mixin to do the event-handling portion of 
    # the main Device class. Kept separate to aid reuse.

    def onEventReceived(self, data):
        eventCode = data[0]
        dlen = data[1]
        if len(data) != dlen+2:
            print ("Invalid length %d in packet: %s" % (dlen, binascii.b2a_hex(data).decode('ascii')))
            return

        if eventCode == E_CMD_RESPONSE:
            (n_cmds, opcode) = struct.unpack("<BH", data[2:5])
            return self.onCommandResponse(n_cmds, opcode, data[5:])
        elif eventCode == E_LE_META_EVENT:
            subEvent = data[2]
            if subEvent == E_LE_CONN_COMPLETE:
                (status, handle, role, peerAddrType, peerAddr, interval, 
                   latency, timeout, masterClock) = struct.unpack("<BHBB6sHHHB", data[3:])
                if status != 0:
                    return self.onConnectionFailed(status, peerAddrType, peerAddr)
                elif role == 0x00:
                    return self.onMasterConnected(handle, peerAddrType, peerAddr)
                elif role == 0x01:
                    return self.onSlaveConnected(handle, peerAddrType, peerAddr)
            elif subEvent == E_LE_ADVERTISING_REPORT:
                n_reports = data[3]
                pos = 4
                for i in range(n_reports):
                    report = AdvertisingReport()
                    pos = report.parseData(data, pos)
                    self.onAdvertisingReport(report)
                return
        elif eventCode == E_DISCONN_COMPLETE:
            (status, handle, reason) = struct.unpack("<BHB", data[2:])
            return self.onDisconnect(status, handle, reason) 
            
        print ("Unhandled event %02X" % eventCode)

    # Stub event handlers   
    def onCommandResponse(self, n_cmds, opcode, params):
        pass

    def onConnectionFailed(self, status, peerAddrType, peerAddr):
        pass

    def onMasterConnected(self, handle, peerAddrType, peerAddr):
        pass

    def onSlaveConnected(self, handle, peerAddrType, peerAddr):
        pass

    def onDisconnect(self, status, handle, reason):
        pass

    def onAdvertisingReport(self, report):
        pass

class AdvertisingReport:
    def __init__(self):
        self.event_type = self.address_type = self.address = self.gap_data = None

    def parseData(self, data, pos):
        hdr = struct.unpack("<BB6sB", data[pos:pos+9])
        (self.event_type, self.address_type, self.address, datalen) = hdr
        self.gap_data = data[pos+9:pos+9+datalen]
        self.RSSI = struct.unpack("<b", data[pos+9+datalen:pos+10+datalen])[0]
        self.adv_data = gap.AdvertisingData(self.gap_data)
        return pos+10+datalen

    def __str__(self):
        return "type=%02X addrtype=%02X addr=%r RSSI=%d adv=%s" % (
            self.event_type, self.address_type, self.address, self.RSSI, self.adv_data)

