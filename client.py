import sys
import socket

import lib.connection as connection
from lib.segment import Segment
import lib.segment as segment

'''
TODO:

Missing Connection constructor implementation
Client init

Missing Connection.send_data implementation
Client init

implement a new function called
check_syn_flag() that returns true or false
based on the syn flag in Segment

Class Segment:
implement a new function called get_seq() that returns the seq part of payload in bytes

Class Segment:
implement a new functionc alled set_seq() that will assign the seq part of payload. Parameter being of type bytes

Segment file:
define a constant SEQ_BYTES that will contain the size of SEQ

Class Segment:
implement a new function called set_ack() that will assign the ack part of payload. Parameter being of type bytes

class Segment:
implement set_syn_flag() that will assign value to the syn_flag with parameter being boolean

class Segment:
implement set_ack_flag() that will assign value to the the ack_flag with parameter being boolean

class Segment:
implement a new function called get_ack() that returns the ack value in boolean
'''

class Client:
    def __init__(self):
        # Init client
        self.client_port = int(sys.argv[1])
        self.broadcast_port = int(sys.argv[2])
        self.path_output = sys.argv[3]

        self.client_connection = Connection("localhost", self.client_port)

        # Output required message
        print(f"[!] Client started at localhost:{self.client_port}")
        pass

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        
        #todo send the first part
        # self.connection.send_syn()
        while True:
            resp: Segment = self.connection.listen_single_segment()

            if resp.check_syn_flag():
                seq = int.from_bytes(resp.get_seq(), 'big')

                syn_ack_sgmt = Segment()
                syn_ack_sgmt.set_seq((300).to_bytes(segment.SEQ_BYTES, 'big'))

                syn_ack_sgmt.set_ack((seq+1).to_bytes(SEQ_BYTES), 'big')

                syn_ack_sgmt.set_syn_flag(True)
                syn_ack_sgmt.set_ack_flag(True)
                self.connection.send_data(syn_ack_sgmt)

            elif resp.get_ack_flag():
                seq = int.from_bytes(sgmt.get_seq(), 'big')

                self.seq = seq
            else:
                seq = int.from_bytes(resp.get_seq(), 'big')

                syn_ack_sgmt = Segment()
                syn_ack_sgmt.set_seq((300).to_bytes(segment.SEQ_BYTES, 'big'))

                syn_ack_sgmt.set_ack((seq+1).to_bytes(SEQ_BYTES), 'big')

                syn_ack_sgmt.set_syn_flag(True)
                syn_ack_sgmt.set_ack_flag(True)
                self.connection.send_data(syn_ack_sgmt, (ip, port))
        pass

    def listen_file_transfer(self):
        # File transfer, client-side
        pass


if __name__ == '__main__':
    if (len(sys.argv) != 4):
        print("[!] client.py could not start. Expected 3 arguments: [client port], [broadcast port], and [path file input].")
    else:
        main = Client()
        main.three_way_handshake()
        main.listen_file_transfer()
