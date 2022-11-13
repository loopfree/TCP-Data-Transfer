import os
import sys
import time
import socket
from lib.connection import Connection
from lib.segment import Segment, SegmentFlag


class Server:
    def __init__(self):
        # Init server
        self.broadcast_port = int(sys.argv[1])
        self.path_file_input = sys.argv[2]
        self.clients = []
        self.server_connection = Connection("localhost", self.broadcast_port)

        # Output required message
        print(f"[!] Server started at localhost:{self.broadcast_port}")
        print(f"[!] Source file | {self.path_file_input} | {os.stat(self.path_file_input).st_size} bytes")
        print(f"[!] Listening to broadcast address for clients.")

    def listen_for_clients(self):
        # Set timeout 15 seconds
        self.server_connection.set_listen_timeout(60)
        # Waiting client for connect
        client_address = []

        is_listening = True
        while is_listening:
            sgmt_payload = self.server_connection.listen_single_segment().get_payload().decode()
            addr = int(sgmt_payload)

            if addr:
                client_address.append(("localhost", addr))
                print(f"[!] Client (localhost:{addr}) discovered")

                while True:
                    accept_more_client = input("[?] Listen for more client? (y/n)")
                    if accept_more_client.lower() == 'n':
                        is_listening = False
                        break
                    if accept_more_client.lower() == 'y':
                        break
                    
                    print("[!] Invalid Input, Try Again")
        
        print(f"{len(client_address)} client(s) discovered")
        print("Details:")
        for index, address in enumerate(client_address):
            print(f"{index+1} {address[0]}:{address[1]}")

        self.clients = client_address

    def start_file_transfer(self):
        # Handshake & file transfer for all clients
        print('[!] Commencing file transfer...')
        for idx, client in enumerate(self.clients):
            if self.three_way_handshake(client):
                self.file_transfer(client)

    def file_transfer(self, client_addr : tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        WINDOW_SIZE = 5
        ACK_TIMEOUT = 10
        seq_base = Segment.INIT_SEQ_NB      # Minimum seq number to be sent (inclusive)
        seq_max = WINDOW_SIZE + seq_base    # Maximum seq number to be sent (exclusive)
        seq_nb = seq_base                   # Current seq number
        ack_nb = 0                          # Last ack number
        chunks = {}                         # Map seq number to data
        chunk_nb = seq_base                 # Current chunk number
        last_chunk_nb = -1                  # Last chunk number of the file
        self.server_connection.set_listen_timeout(0.5)
        last_recv_time = time.time()

        with open(self.path_file_input, "rb") as in_file:
            while True:
                # Receive ACK
                try:
                    recv_segment = self.server_connection.listen_single_segment()
                    if not recv_segment.get_flag().is_ack_flag():
                        raise TypeError
                    
                    ack_nb = recv_segment.get_header()["ack_nb"]
                    if ack_nb == last_chunk_nb:     # Finished transfering file
                        break

                    if ack_nb >= seq_base:
                        seq_base = ack_nb + 1
                        seq_max = WINDOW_SIZE + seq_base
                        last_recv_time = time.time()
                        print(f"[!] [File Transfer] Received ACK {ack_nb}")

                        # Delete old chunk from buffer
                        for nb in list(chunks):
                            if nb < seq_base:
                                chunks.pop(nb)
                except:
                    pass

                # Add chunk to buffer
                if chunk_nb < seq_max:
                    chunk = in_file.read(Segment.MAX_PAYLOAD_SIZE)
                    if chunk:
                        chunks[chunk_nb] = chunk
                        chunk_nb += 1
                    else:
                        last_chunk_nb = chunk_nb
                
                # Check timeout
                if time.time() - last_recv_time > ACK_TIMEOUT:
                    seq_nb = seq_base
                
                # Send chunk
                if chunks and seq_base <= seq_nb < seq_max:
                    try:
                        sent_segment = Segment()
                        sent_segment.set_header({"seq_nb": seq_nb})
                        sent_segment.set_payload(chunks[seq_nb])
                        self.server_connection.send_data(sent_segment, client_addr)
                        print(f"[!] [File Transfer] Sending segment {seq_nb}")
                        seq_nb += 1
                    except:
                        pass

        # Close connection
        fin_segment = Segment()
        fin_segment.set_flag([SegmentFlag.FIN_FLAG])
        self.server_connection.send_data(fin_segment, client_addr)


    def three_way_handshake(self, client_addr: tuple[str, int]) -> bool:
        # Three way handshake, server-side, 1 client
        print(f'[!] [Handshake] Handshake to client ({client_addr[0]}:{client_addr[1]}) ...')
        # SYN
        # Send SYN
        try:
            syn_sgmt = Segment()
            syn_sgmt.set_header({"seq_nb": 100})
            syn_sgmt.set_flag([SegmentFlag.SYN_FLAG])
            self.server_connection.send_data(syn_sgmt, client_addr)
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] SYN Segment Sent")
        except socket.timeout:
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] SYN Timeout")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] SYN Segment Send Failed")

            return False


        # SYN-ACK
        # Wait SYN-ACK (internal function)
        try:
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Waiting For Segment SYN-ACK")
            syn_ack_segment = self.server_connection.listen_single_segment()
            sgmt : Segment = syn_ack_segment
        except socket.timeout:
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] SYN-ACK Timeout")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Failed")

            return False


        # ACK
        # Receive ACK
        try:
            if sgmt.get_flag().is_syn_flag() and sgmt.get_flag().is_ack_flag():
                print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Segment SYN-ACK Received")

                ack_sgmt = Segment()
                ack_sgmt.set_header({'ack_nb': sgmt.get_header()['seq_nb'] + 1})
                ack_sgmt.set_flag([SegmentFlag.ACK_FLAG])

                self.server_connection.send_data(ack_sgmt, client_addr)
                print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Send Segment ACK")
                print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Succeed, Starting The Data Transfer..")
                
                return True
            
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Unidentified Segment Detected")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Failed")
            
            return False

        except socket.timeout:
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] ACK Timeout")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Unable To Send Segment ACK")
            print(f"[({client_addr[0]}:{client_addr[1]}) THREE WAY HANDSHAKE] Failed, Cannot Proceed To Data Transfer")

            return False



if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print("[!] server.py could not start. Expected 2 arguments: [broadcast port] and [path file input].")
    else:
        main = Server()
        main.listen_for_clients()
        main.start_file_transfer()
