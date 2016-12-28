import sys
import os
import socket
import binascii
import select
import struct

import hcipacket


class HCISocket:
    MAX_PACKET_LEN = 256

    def __init__(self, devId):
        self.devId = devId
        self.delegate = None
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
        self.sock.bind( (devId,) )
        filt = struct.pack("@LLLH", # struct hci_filter
                    0x14, # type_mask
                    0xC120, 0x40000000, # event_mask[2]
                    0 ) # opcode
        self.sock.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, filt)
        self.packetQueue = []
        self.poller = select.poll()
        self.poller.register(self.sock)
        self.running = False

    def withDelegate(self, d):
        self.delegate = d
        return self

    def queuePacket(self, packet):
        self.packetQueue.append(packet)

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if len(self.packetQueue) > 0:
                self.poller.modify(self.sock, (select.POLLIN|select.POLLOUT|select.POLLERR))
            else:
                self.poller.modify(self.sock, (select.POLLIN|select.POLLERR))
            print ("Wait...")
            evts = self.poller.poll(1000.0)
            for (fd, evtmask) in evts:
                if (evtmask & select.POLLERR):
                    print ("Error on socket, exiting")
                    self.running = False
                    break
                if (evtmask & select.POLLOUT) and len(self.packetQueue) > 0:
                    pkt = self.packetQueue.pop(0)
                    print ("Sending:" + str(pkt))
                    self.sock.send( pkt.toBytes() )
                if (evtmask & select.POLLIN):
                    pktbuf = self.sock.recv(self.MAX_PACKET_LEN)
                    pkt = hcipacket.HCIPacket.fromBytes(pktbuf)
                    print ("Got:" + str(pkt))
                    self.delegate.onPacketReceived(self, pkt)




