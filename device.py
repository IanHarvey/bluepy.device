import struct
import binascii

import hcipacket
import commands

EVENT_CMD_RESPONSE = 0x0E
EVENT_LE_EVENT = 0x3E

class Device:
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
            self.onEventReceived(pkt.payload)
        else:
            print ("Unhandled packet")

    def onEventReceived(self, data):
        eventCode = data[0]
        dlen = data[1]
        if len(data) != dlen+2:
            print ("Invalid length %d in packet: %s" % (dlen, binascii.b2a_hex(data).decode('ascii')))
            return
        if eventCode == EVENT_CMD_RESPONSE:
            self.onCommandResponse(data)
        else:
            print ("Unhandled event")

   
    def onCommandResponse(self, data):
        (nCmds, opcode) = struct.unpack("<BH", data[2:5])
        # Do sth with nCmds
        if opcode in self.commandMap:
            self.commandMap.pop(opcode).onResponse(data[5:])
        else:
            print ("Unhandled opcode")

    # Various bits of state machine

    def start(self):
        assert (self.hciSocket is not None)
        self.queueCommand( commands.ReadLocalVersion().withCompletion(self.st_got_version) )
        return self.run()

    def st_got_version(self, cmd):
        print ("Response is: " + str(cmd))
        self.stop()

if __name__ == '__main__':
    from hcisocket_linux import HCISocket
    dev = Device().withSocket( HCISocket(devId=0) )
    dev.start()

