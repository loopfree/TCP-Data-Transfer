from lib.connection import Segment, Connection
import lib.connection as connection
import sys

'''
TODO:

class Connection:
add one more parameter which stands for
"isServer"
if it is true, then the socket will be made for a server
'''

class Server:
    def __init__(self):
        # Init server
        self.broadcast_port = int(sys.argv[1])
        self.path_file_input = sys.argv[2]
        
        self.server_connection = Connection("localhost", self.broadcast_port)

        # Output required message
        print(f"[!] Server started at localhost:{self.broadcast_port}")
        print(f"[!] Source file | {self.path_file_input} | {0} bytes")
        print(f"[!] Listening to broadcast address for clients.")
        pass

    def listen_for_clients(self):
        # Waiting client for connect
        pass

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr : ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: ("ip", "port")) -> bool:
        # Three way handshake, server-side, 1 client
        syn_sgmt = Segment()
        syn_sgmt.set_seq((100).to_bytes(SEQ_BYTES, 'big'))

        syn_sgmt.set_syn_flag(True)
        self.connection.send_data(syn_sgmt, client_addr)
        pass


if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print("[!] server.py could not start. Expected 2 arguments: [broadcast port] and [path file input].")
    else:
        main = Server()
        main.listen_for_clients()
        main.start_file_transfer()
