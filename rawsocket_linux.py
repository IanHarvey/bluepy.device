import sys
import os
import socket
import binascii

if __name__ == '__main__':
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI);
    devId = 0

    s.bind( (devId,) )

    s.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, binascii.a2b_hex("1400000020c10000000000400000"))

    print( "Writing" )
    s.send( binascii.a2b_hex("01011000") )

    print ( "Reading" )
    v  = s.recv(256)

    print ("Got: " + str(binascii.b2a_hex(v)) )
