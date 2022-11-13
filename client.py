import sys
import time
from lib.connection import Connection
from lib.segment import Segment, SegmentFlag


class Client:
    def __init__(self):
        # Init client
        self.client_port = int(sys.argv[1])
        self.broadcast_port = int(sys.argv[2])
        self.path_output = sys.argv[3]

        self.client_connection = Connection("localhost", self.client_port)

        self.seq_number = Segment.INIT_SEQ_NB

        # Output required message
        print(f"[!] Client started at localhost:{self.client_port}")

        # Kirim request ke server
        request_message = Segment()
        request_message.set_payload(f'{self.client_port}'.encode())
        self.client_connection.send_data(request_message, ("localhost", self.broadcast_port))

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        # Inisialisasi dimulai dari server, tunggu request.
        print("[!] [Handshake] Waiting for SYN request...")
        req_segment = self.client_connection.listen_single_segment()

        while not req_segment.get_flag().is_syn_flag():
            req_segment = self.client_connection.listen_single_segment()

        req_header = req_segment.get_header()
        print("[!] [Handshake] SYN request received")

        # Kirim SYN-ACK
        print(f"[!] [Handshake] Sending broadcast SYN-ACK reply to port {self.broadcast_port}")
        reply_segment = Segment()
        reply_segment.set_header({
            "seq_nb": self.seq_number,
            "ack_nb": req_header["seq_nb"] + 1
        })
        reply_segment.set_flag([SegmentFlag.SYN_FLAG, SegmentFlag.ACK_FLAG])
        print("[!] [Handshake] Waiting for response...")
        self.client_connection.send_data(reply_segment, ("localhost", self.broadcast_port))
        self.seq_number += 1

        # Tunggu ACK
        reply_segment = self.client_connection.listen_single_segment()

        while not reply_segment.get_flag().is_ack_flag():
            reply_segment = self.client_connection.listen_single_segment()

        print("[!] [Handshake] ACK reply received")
        return

    def listen_file_transfer(self):
        # File transfer, client-side
        ack_nb = Segment.INIT_ACK_NB
        SEQ_TIMEOUT = 30
        last_recv_nb = ack_nb - 1
        last_recv_time = time.time()
        self.client_connection.set_listen_timeout(10)

        with open(self.path_output, "wb") as out_file:
            while True:
                try:
                    # Receive segment
                    file_segment = self.client_connection.listen_single_segment()
                    last_recv_time = time.time()

                    # Finish receiving file
                    if file_segment.get_flag().is_fin_flag():
                        break
                        
                    # Check segment
                    if file_segment.get_header()["seq_nb"] == ack_nb and file_segment.valid_checksum():
                        out_file.write(file_segment.get_payload())
                        print(f"[!] [File Transfer] Received segment {ack_nb}")
                        last_recv_nb = ack_nb
                        ack_nb += 1
                
                finally:
                    if last_recv_nb > 0:
                        # Send ACK
                        ack_segment = Segment()
                        ack_segment.set_header({"ack_nb": last_recv_nb})
                        ack_segment.set_flag([SegmentFlag.ACK_FLAG])
                        self.client_connection.send_data(ack_segment, ("localhost", self.broadcast_port))
                        print(f"[!] [File Transfer] Sending ACK {last_recv_nb} to server")
                
                # Force close connection on timeout
                if time.time() - last_recv_time > SEQ_TIMEOUT:
                    break
        
        self.client_connection.close_socket()
        return

if __name__ == '__main__':
    if (len(sys.argv) != 4):
        print("[!] client.py could not start. Expected 3 arguments: [client port], [broadcast port], and [path file input].")
    else:
        main = Client()
        main.three_way_handshake()
        main.listen_file_transfer()
