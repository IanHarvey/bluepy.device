import struct
import binascii

import hcipacket
import commands
import events

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
            else:
                nextCmd = commands.LESetEventMask(events.DEFAULT_LE_EVENT_MASK)
        elif (self.startup_state == 3):
            nextCmd = commands.WriteLEHostSupported(commands.WriteLEHostSupported.LE_ENABLE, commands.WriteLEHostSupported.LE_SIMUL_DISABLE)

        if nextCmd:
            self.startup_state += 1
            self.queueCommand(nextCmd.withCompletion(self.startup_next_state))
        else:
            print ("Stopping")
            self.stop()

if __name__ == '__main__':
    from hcisocket_linux import HCISocket
    dev = Device().withSocket( HCISocket(devId=0) )
    dev.start()

