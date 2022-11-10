from mp import Manager, Process

from lib.connection import Segment, Connection, SEQ_BYTES
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
        client_address = []
        client_handled = []

        is_listening = True
        while is_listening:
            msg, addr = self.connection.listen_single_segment()

            if addr:
                client_address.append(addr)
                client_handled.append(False)
                print(f"[!] Client ({addr[0]}:{addr[1]}) discovered")

                while True:
                    accept_more_client = input("[?] Listen for more client? (y/n)")
                    if accept_more_client.lower() == 'n':
                        is_listening = False
                        break
                    if accept_more_client.lower() == 'y':
                        break
                    
                    print('[!] Invalid Input, Try Again')
        
        print(f"{len(client_address)} client(s) discovered")
        print("Details:")
        for address, index in enumerate(client_address):
            print(f"{index+1} {address[0]}:{address[1]}")

        return client_address, client_handled
        pass

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr : tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: tuple[str, int]) -> bool:
        # Three way handshake, server-side, 1 client

        # SYN
        # Send SYN
        syn_sgmt = Segment()
        syn_sgmt.set_seq((100).to_bytes(SEQ_BYTES, 'big'))

        syn_sgmt.set_syn_flag(True)
        self.connection.send_data(syn_sgmt, client_addr)
        print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] SYN Segment Sent")

        # SYN-ACK
        # Wait SYN-ACK (internal function)
        print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Waiting For Segment SYN-ACK")
        def wait_ack_syn(return_map):
            return_map["segment"] = self.connection.listen_single_segment()

        manager = Manager()
        return_map = manager.dict()
        sgmt_wait_ack_syn = Process(target = wait_ack_syn, args=(return_map, ))

        # Start waiting
        # Timeout = 5s
        sgmt_wait_ack_syn.start()
        sgmt_wait_ack_syn.join(5)
        
        if sgmt_wait_ack_syn.is_alive():
            sgmt_wait_ack_syn.kill()
        
            return -1

        sgmt = return_map["segment"]

        # ACK
        # Receive ACK
        if sgmt.get_syn_flag() and sgmt.get_ack_flag():
            seq = int.from_bytes(sgmt.get_seq(), 'big')
            ack = int.from_bytes(sgmt.get_ack(), 'big')
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Segment ACK Received")

            ack_sgmt = Segment()
            ack_sgmt.set_seq(ack.to_bytes(SEQ_BYTES, 'big'))

            ack_sgmt.set_ack((seq+1).to_bytes(SEQ_BYTES), 'big')

            ack_sgmt.set_ack_flag(True)

            self.connection.send_data(ack_sgmt, client_addr)
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Send Segment ACK")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Succeed, Starting The Data Transfer..")
            
            return ack
        
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Unidentified Segment Detected")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Failed")
        return -1
        pass


if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print("[!] server.py could not start. Expected 2 arguments: [broadcast port] and [path file input].")
    else:
        main = Server()
        main.listen_for_clients()
        main.start_file_transfer()
