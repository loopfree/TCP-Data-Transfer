import sys, os
from lib.connection import Segment, Connection
from lib.segment import SYN_FLAG, ACK_FLAG, FIN_FLAG

def int_to_bytes(num):
    return num.to_bytes(1, 'big')

class Server:
    def __init__(self):
        # Init server
        self.broadcast_port = int(sys.argv[1])
        self.path_file_input = sys.argv[2]
        
        self.server_connection = Connection("localhost", self.broadcast_port)

        self.client_list = []

        self.seq_number = 0
        
        # Output required message
        print(f"[!] Server started at localhost:{self.broadcast_port}")
        print(f"[!] Source file | {self.path_file_input} | {os.stat(self.path_file_input).st_size} bytes")
        print(f"[!] Listening to broadcast address for clients.")
        pass

    def listen_for_clients(self):
        # Waiting client for connect``
        while True:
            req_segment = self.server_connection.listen_single_segment()
            # Konvensi:
            # Request message memiliki flag b'\x00'.
            # Pada payload, ada port requester.
            if (req_segment.get_flag().get_flag_bytes() == b'\x00'):
                client_port = int(req_segment.get_payload().decode())

                print(f'[!] Received request from 127.0.0.1:{client_port}')

                self.client_list.append(("127.0.0.1", client_port))

                listen_prompt = input("[?] Listen more? (y/n) ")

                while listen_prompt != 'y' and listen_prompt != 'n':
                    listen_prompt = input("[?] Listen more? (y/n) ")

                if (listen_prompt == 'n'):
                    print()
                    print('Client list:')
                    for idx, client in enumerate(self.client_list):
                        print(f'{idx + 1}. {client[0]}:{client[1]}')
                    print()
                    break
            else:
                break

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        print('[!] Commencing file transfer...')

        for idx, client in enumerate(self.client_list):
            print(f'[!] [Handshake] Handshake to client {idx + 1}...')

            self.three_way_handshake(client)
            self.file_transfer(client)
        pass

    def file_transfer(self, client_addr : tuple[str, int]):
        # File transfer, server-side, Send file to 1 client
        MAXIMUM_PAYLOAD = 32756
        # Read bytes dari path_file_input
        with open(self.path_file_input, "rb") as in_file:
            while True:
                chunk = in_file.read(MAXIMUM_PAYLOAD)

                if chunk == b"":
                    fin_segment = Segment()
                    fin_segment.set_flag([FIN_FLAG])
                    self.server_connection.send_data(fin_segment, client_addr)
                    break
                
                # Kirim chunk ke client_addr
                sent_segment = Segment()
                sent_segment.set_payload(chunk)

                self.server_connection.send_data(sent_segment, client_addr)
        
        return

    def three_way_handshake(self, client_addr: tuple[str, int]) -> bool:
        # Three way handshake, server-side, 1 client
        # Inisialisasi handshake dimulai dari server
        print(f'[!] [Handshake] Sending unicast SYN request to port {client_addr[1]}')

        syn_segment = Segment()
        syn_segment.set_header({
            "seq_nb": self.seq_number,
            "ack_nb": 0
        })
        syn_segment.set_flag([SYN_FLAG])
        self.server_connection.send_data(syn_segment, client_addr)
        self.seq_number += 1

        # Menunggu SYN-ACK reply
        print("[!] [Handshake] Waiting for response...")
        reply_segment = self.server_connection.listen_single_segment()

        while reply_segment.get_flag().get_flag_bytes() != int_to_bytes(SYN_FLAG | ACK_FLAG):
            reply_segment = self.server_connection.listen_single_segment()

        print("[!] [Handshake] SYN-ACK reply received")
        reply_header = reply_segment.get_header()

        # Kirim ACK
        print(f"[!] [Handshake] Sending unicast ACK reply to port {client_addr[1]}")

        ack_segment = Segment()
        ack_segment.set_header({
            "seq_nb": self.seq_number,
            "ack_nb": reply_header["seq_nb"] + 1
        })
        ack_segment.set_flag([ACK_FLAG])
        self.server_connection.send_data(ack_segment, client_addr)
        self.seq_number += 1
        return

if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print("[!] server.py could not start. Expected 2 arguments: [broadcast port] and [path file input].")
    else:
        if (not os.path.exists(sys.argv[2])):
            print("[!] server.py could not start. Path file input doesn't exist!")
        else:
            main = Server()
            main.listen_for_clients()
            main.start_file_transfer()