import struct
import binascii

import hcipacket
import commands
import events
import gap

class Device(events.EventHandler):
    def __init__(self):
        self.commandMap = {}  # Maps opcode to command objects
        self.hciSocket = None

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
        else:
            print ("Unhandled packet")

    # Event handling
    def onCommandResponse(self, n_cmds, opcode, params):
        # TODO: do sth with n_cmds
        if opcode in self.commandMap:
            self.commandMap.pop(opcode).onResponse(params)
        else:
            print ("Unhandled opcode 0x%04X" % opcode)

    # Various bits of state machine

    def start(self):
        assert (self.hciSocket is not None)
        self.startup_state = 0
        self.startup_next_state(None)

        self.adv = gap.AdvertisingData()
        self.adv.addItem(gap.GAP_FLAGS, [0x06])
        self.adv.addItem(gap.GAP_UUID_128BIT_INCOMPLETE, b'\xF0\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF')
        self.scn = gap.AdvertisingData()
        self.scn.addItem(gap.GAP_NAME_INCOMPLETE, 'test'.encode('ascii'))
        print ("adv=", binascii.b2a_hex(self.adv.data))
        print ("scn=", binascii.b2a_hex(self.scn.data))
        return self.run()

    def startup_next_state(self, cmd):
        nextCmd = None
        if (cmd is not None) and cmd.error():
            print ("Error from command (opc=0x%04X) : %s" % (cmd.opcode, cmd.error()))
            self.stop()
        elif (self.startup_state == 0):
            nextCmd = commands.SetEventMask(events.DEFAULT_EVENT_MASK)
        elif (self.startup_state == 1):
            nextCmd = commands.ReadLocalVersion()
        elif (self.startup_state == 2):
            if cmd.version < commands.ReadLocalVersion.BLUETOOTH_V4_0:
                print ("Bluetooth 4.0 unsupported")
                self.stop()
            else:
                nextCmd = commands.LESetEventMask(events.DEFAULT_LE_EVENT_MASK)
        elif (self.startup_state == 3):
            nextCmd = commands.WriteLEHostSupported(commands.WriteLEHostSupported.LE_ENABLE, commands.WriteLEHostSupported.LE_SIMUL_DISABLE)
        elif (self.startup_state == 4):
            nextCmd = commands.LESetAdvertisingParameters()
        elif (self.startup_state == 5):
            nextCmd = commands.LESetAdvertisingData(self.adv.data)
        elif (self.startup_state == 6):
            nextCmd = commands.LESetScanResponseData(self.scn.data)
        elif (self.startup_state == 7):
            nextCmd = commands.LESetAdvertiseEnable(commands.LESetAdvertiseEnable.ENABLE)

        if nextCmd:
            self.startup_state += 1
            self.queueCommand(nextCmd.withCompletion(self.startup_next_state))
        else:
            print ("All done")

if __name__ == '__main__':
    from hcisocket_linux import HCISocket
    dev = Device().withSocket( HCISocket(devId=0) )
    dev.start()

