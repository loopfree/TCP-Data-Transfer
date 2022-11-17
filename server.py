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
        self.server_connection.set_listen_timeout(15)
        # Waiting client for connect
        client_address = []

        is_listening = True
        while is_listening:
            try:
                sgmt_payload = self.server_connection.listen_single_segment().get_payload().decode()
                addr = int(sgmt_payload)

                if addr:
                    client_address.append(("localhost", addr))
                    print(f"[!] Client (localhost:{addr}) discovered")

                    while True:
                        accept_more_client = input("[?] Listen for more client? (y/n) ")
                        if accept_more_client.lower() == 'n':
                            is_listening = False
                            break
                        if accept_more_client.lower() == 'y':
                            break
                        
                        print("[!] Invalid input, try again")
            except socket.timeout:
                print(f"[!] Timeout, stopped listening for clients")
                break
        
        print(f"{len(client_address)} client(s) discovered")
        print("Details:")
        for index, address in enumerate(client_address):
            print(f"{index+1} {address[0]}:{address[1]}")

        self.clients = client_address

    def start_file_transfer(self):
        # Handshake & file transfer for all clients
        print('[!] Commencing file transfer...')
        for client in self.clients:
            if self.three_way_handshake(client):
                self.file_transfer(client)
                self.four_way_handshake(client)

    def file_transfer(self, client_addr : tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        WINDOW_SIZE = 5
        ACK_TIMEOUT = 1                         # Maximum time to wait for acknowledgments
        FILE_TRANSFER_TIMEOUT = 30              # If file transfer commences above this, it will result as failed
        seq_base = Segment.INIT_SEQ_NB          # Start of window
        seq_max = WINDOW_SIZE + seq_base - 1    # End of window
        seq_num = seq_base                      # Sequence number to send
        last_seq_num = None                     # Biggest seq num that can be sent
        last_ack_time = time.time()             # Last ack timestamp
        chunk = {}                              # File chunks

        print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] Initiating file transfer ...')
        self.server_connection.set_listen_timeout(ACK_TIMEOUT)

        with open(self.path_file_input, "rb") as in_file:
            # Kirim segmen-segmen awal!
            while (seq_num <= seq_max):       
                read_chunk = in_file.read(Segment.MAX_PAYLOAD_SIZE)
                if read_chunk:
                    chunk[seq_num] = read_chunk
                    file_segment = Segment()
                    file_segment.set_header({
                        "seq_nb": seq_num
                    })
                    file_segment.set_payload(chunk[seq_num])
                    self.server_connection.send_data(file_segment, client_addr)
                    print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] [Num = {seq_num}] Sending segment to client ...')
                    seq_num += 1
                else:
                    if not last_seq_num:
                        last_seq_num = seq_num - 1
                    break

            while True:
                if time.time() - last_ack_time > FILE_TRANSFER_TIMEOUT:
                    print(f"[!] [Client {client_addr[0]}:{client_addr[1]}] File transfer timeout, aborting transfer")
                    break

                try:
                    recv_segment = self.server_connection.listen_single_segment()

                    if not recv_segment.get_flag().is_ack_flag() or not recv_segment.valid_checksum():
                        # Message tidak valid!
                        raise ValueError

                    # Baca header dari ACK -- khususnya ack number.
                    ack_number = recv_segment.get_header()['ack_nb']
                    if ack_number >= seq_base + 1:
                        seq_max = (seq_max - seq_base) + ack_number
                        seq_base = ack_number
                        last_ack_time = time.time()
                        print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] [Num = {seq_base}] [ACK] ACK received, new sequence base = {seq_base + 1}')
                        
                        # Delete dari chunk ...
                        for key in list(chunk):
                            if key < seq_base:
                                del chunk[key]

                except (socket.timeout, ValueError):
                    # ACK tidak ditemukan. Ulangi pengiriman ,,,
                    print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] [Num = {seq_base}] [Timeout] ACK response timeout/invalid ACK number, resending segment ...')
                    seq_num = seq_base

                # Send sequence number terakhir ...
                if seq_num <= seq_max:    
                    read_chunk = None
                    if seq_num in chunk:
                        read_chunk = chunk[seq_num]
                    else:
                        read_chunk = in_file.read(Segment.MAX_PAYLOAD_SIZE)
                    
                    if read_chunk:
                        print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] [Num = {seq_num}] Sending segment to client ...')
                        chunk[seq_num] = read_chunk
                        file_segment = Segment()
                        file_segment.set_header({
                            "seq_nb": seq_num
                        })
                        file_segment.set_payload(chunk[seq_num])
                        self.server_connection.send_data(file_segment, client_addr)
                        seq_num += 1
                    else:
                        if not last_seq_num:
                            last_seq_num = seq_num - 1
                        
                        if ack_number == last_seq_num + 1:
                            # Sudah tidak ada lagi yang bisa dibaca.
                            print(f'[!] [Client {client_addr[0]}:{client_addr[1]}] [CLS] File transfer completed. Initiating closing connection ...')
                            return
                        else:
                            # Masih ada ACK lain yang harus diterima
                            continue 

    def three_way_handshake(self, client_addr: tuple[str, int]) -> bool:
        # Three way handshake, server-side, 1 client
        '''
            How this works:
            (1) Server starts the three-way handshake
            (2) When listening for SYN-ACK segments, maximum timeout is 1 second. If timeout happens, restart handshake.
            (3) If three-way handshake takes longer than 15 seconds, mark process as failed.
        '''
        WAIT_FOR_SYN_ACK = 1        # 1 seconds
        HANDSHAKE_TIME_LIMIT = 120  # 120 seconds
        start_handshake_time = time.time()

        self.server_connection.set_listen_timeout(WAIT_FOR_SYN_ACK)

        print(f'[!] [Three-Way Handshake] Starting three-way handshake to client {client_addr[0]}:{client_addr[1]} ...')

        while True:
            # Check if timeout limit reached
            if time.time() - start_handshake_time > HANDSHAKE_TIME_LIMIT:
                print(f'[!] Could not establish connection with client {client_addr[0]}:{client_addr[1]}. Skipping client ...')
                return False

            # Send SYN segment
            syn_sgmt = Segment()
            syn_sgmt.set_header({"seq_nb": 100})
            syn_sgmt.set_flag([SegmentFlag.SYN_FLAG])
            self.server_connection.send_data(syn_sgmt, client_addr)
            print(f"[!] [Three-Way Handshake] SYN segment sent to {client_addr[0]}:{client_addr[1]}!")

            # Wait for SYN-ACK
            try:
                print(f"[!] [Three-Way Handshake] Waiting for SYN-ACK segment from {client_addr[0]}:{client_addr[1]} ...")
                syn_ack_sgmt = self.server_connection.listen_single_segment()
            except socket.timeout:
                print(f"[!] [Three-Way Handshake] Did not receive SYN-ACK segment from {client_addr[0]}:{client_addr[1]}, retrying ... ")
                continue

            # Receive SYN-ACK
            # Then Send ACK
            if syn_ack_sgmt.get_flag().is_syn_flag() and syn_ack_sgmt.get_flag().is_ack_flag():
                print(f"[!] [Three-Way Handshake] Received SYN-ACK segment from {client_addr[0]}:{client_addr[1]}!")

                ack_sgmt = Segment()
                ack_sgmt.set_header({'ack_nb': syn_ack_sgmt.get_header()['seq_nb'] + 1})
                ack_sgmt.set_flag([SegmentFlag.ACK_FLAG])

                self.server_connection.send_data(ack_sgmt, client_addr)
                print(f"[!] [Three-Way Handshake] Sent ACK segment to {client_addr[0]}:{client_addr[1]}!")
                print(f"[!] [Three-Way Handshake] Connection established. Sending data to client ...")
                
                return True
            else:
                print(f"[!] [Three-Way Handshake] Wrong segment received. Expected SYN-ACK from {client_addr[0]}:{client_addr[1]}, retrying ... ")
                continue

    def four_way_handshake(self, client_addr: tuple[str, int]):
        # Tearing the session
        print(f"[!] [Four-Way Handshake] Start session closing")

        self.server_connection.set_listen_timeout(1)
        MAX_FWH_TIME = 10
        fwh_start = time.time()


        while True:
            if time.time() - fwh_start > MAX_FWH_TIME:
                print("[!] [Four-Way Handshake] Timeout limit for four way handshake reached. Closing connection ...")
                break

            # Send FIN
            fin_sgmt = Segment()
            fin_sgmt.set_header({"seq_nb": 100})
            fin_sgmt.set_flag([SegmentFlag.FIN_FLAG])
            self.server_connection.send_data(fin_sgmt, client_addr)
            print(f"[!] [Four-Way Handshake] FIN segment sent")

            # Wait For ACK
            try:
                print(f"[!] [Four-Way Handshake] Waiting for segment ACK")
                ack_segment = self.server_connection.listen_single_segment()
                if not ack_segment.get_flag().is_ack_flag():
                    continue
                print(f"[!] [Four-Way Handshake] ACK segment received")
                break
            except socket.timeout:
                print(f"[!] [Four-Way Handshake] ACK timeout")
                print(f"[!] [Four-Way Handshake] Failed")
                continue
        
        while True:
            if time.time() - fwh_start > MAX_FWH_TIME:
                print("[!] [Four-Way Handshake] Timeout limit for four way handshake reached. Closing connection ...")
                break
            
            # Wait For FIN
            try:
                print(f"[!] [Four-Way Handshake] Waiting for FIN segment")
                fin_segment = self.server_connection.listen_single_segment()
                if not fin_segment.get_flag().is_fin_flag():
                    continue
                print(f"[!] [Four-Way Handshake] FIN segment received")
            except socket.timeout:
                print(f"[!] [Four-Way Handshake] FIN timeout")
                print(f"[!] [Four-Way Handshake] Failed")
                continue

            # Send ACK
            ack_sgmt = Segment()
            ack_sgmt.set_flag([SegmentFlag.ACK_FLAG])
            self.server_connection.send_data(ack_sgmt, client_addr)
            print(f"[!] [Four-Way Handshake] ACK segment sent")
            print(f"[!] [Four-Way Handshake] Connection closed")
            break

if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print("[!] server.py could not start. Expected 2 arguments: [broadcast port] and [path file input].")
    else:
        main = Server()
        main.listen_for_clients()
        main.start_file_transfer()
