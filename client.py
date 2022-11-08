import sys
from lib.connection import Segment, Connection

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
