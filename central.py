import struct
import binascii

import hcipacket
import commands
import events

class Central(events.EventHandler):
    def __init__(self):
        # TODO: refactor commandMap 
        self.commandMap = {}  # Maps opcode to command objects
        self.hciSocket = None
        self.connection = None

    def withSocket(self, sock):
        self.hciSocket = sock.withDelegate(self)
        return self

    def run(self):
        self.hciSocket.run()
        return self

    def stop(self):
        self.hciSocket.stop()
        print ("Stopping")

    def queueCommand(self, cmd):
        if cmd.opcode in self.commandMap:
            print("Cmd 0x%04X already in progress", cmd.opcode)
            return
        self.commandMap[cmd.opcode] = cmd
        self.hciSocket.queuePacket(cmd.getPacket())        

    def onPacketReceived(self, sock, pkt):
        print ("Delegate called: " + str(pkt))
        if pkt.packetType == hcipacket.HCI_EVENT_PACKET:
            self.onEventReceived(pkt.payload) # Handled by events.EventHandler mixin
        elif pkt.packetType == hcipacket.HCI_ACL_DATA_PACKET and self.connection is not None:
            chan = pkt.getAclChannel()
            # FIXME - look up by channel
            self.connection.onReceivedData(pkt.payload)
        else:
            print ("Unhandled packet")

    # Event handling
    def onCommandResponse(self, n_cmds, opcode, params):
        # TODO: do sth with n_cmds
        if opcode in self.commandMap:
            self.commandMap.pop(opcode).onResponse(params)
        else:
            print ("Unhandled opcode 0x%04X" % opcode)

    def onSlaveConnected(self, handle, peerAddrType, peerAddr):
        print ("Slave connected, handle=0x%04X" % handle)
        self.connection = (hcipacket.ACLConnection(self.hciSocket, handle)
                              .withChannel(gatt.CID_GATT, self.gatt.onMessageReceived)
                           ) # FIXME. put in dict

    def onDisconnect(self, status, handle, reason):
        if status != 0x00:
            print ("Disconnect failed (err=0x%02X)" % status)
        elif self.connection is None or handle != self.connection.handle:
            print ("Disconnect when apparently not connected? handle=0x%04X" % handle)
        else:
            self.connection.onDisconnect(reason)
        
    def onAdvertisingReport(self, report):
        print ("Reports received:" + str(report))

    # Various bits of state machine

    def start(self):
        assert (self.hciSocket is not None)

        self.startup_state = 0
        self.startup_next_state(None)
        return self.run()

    def startup_next_state(self, cmd):
        print ("startup_next_state", self.startup_state)
        nextCmd = None
        if (cmd is not None) and cmd.error():
            print ("Error from command (opc=0x%04X) : %s" % (cmd.opcode, cmd.error()))
            self.stop()
        elif (self.startup_state == 0):
            nextCmd = commands.Reset()
        elif (self.startup_state == 1):
            nextCmd = commands.SetEventMask(events.DEFAULT_EVENT_MASK)
        elif (self.startup_state == 2):
            nextCmd = commands.ReadLocalVersion()
        elif (self.startup_state == 3):
            if cmd.version < commands.ReadLocalVersion.BLUETOOTH_V4_0:
                print ("Bluetooth 4.0 unsupported")
                self.stop()
            else:
                lemask = events.DEFAULT_LE_EVENT_MASK
                lemask |= events.eventMask([events.E_LE_ADVERTISING_REPORT])
                nextCmd = commands.LESetEventMask(lemask)
        elif (self.startup_state == 4):
            nextCmd = commands.WriteLEHostSupported(commands.WriteLEHostSupported.LE_ENABLE, commands.WriteLEHostSupported.LE_SIMUL_DISABLE)

        # Scan-specific stuff starts here...
        elif (self.startup_state == 5):
            nextCmd = commands.LESetScanParameters(scan_type=commands.LESetScanParameters.ACTIVE)
        elif (self.startup_state == 6):
            nextCmd = commands.LESetScanEnable(commands.LESetScanEnable.ENABLE)

        if nextCmd:
            self.startup_state += 1
            self.queueCommand(nextCmd.withCompletion(self.startup_next_state))
        else:
            print ("All done")

if __name__ == '__main__':
    from hcisocket_linux import HCISocket
    dev = Central().withSocket( HCISocket(devId=0) )
    dev.start()

