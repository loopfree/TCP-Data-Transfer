import sys
from lib.connection import Segment, Connection
from lib.segment import SYN_FLAG, ACK_FLAG, FIN_FLAG

def int_to_bytes(num):
    return num.to_bytes(1, 'big')

class Client:
    def __init__(self):
        # Init client
        self.client_port = int(sys.argv[1])
        self.broadcast_port = int(sys.argv[2])
        self.path_output = sys.argv[3]

        self.client_connection = Connection("localhost", self.client_port)

        self.seq_number = 0

        # Output required message
        print(f"[!] Client started at localhost:{self.client_port}")

        # Kirim request ke server
        request_message = Segment()
        request_message.set_payload(f'{self.client_port}'.encode())
        self.client_connection.send_data(request_message, ("localhost", self.broadcast_port))
        pass

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        # Inisialisasi dimulai dari server, tunggu request.
        print("[!] [Handshake] Waiting for SYN request...")
        req_segment = self.client_connection.listen_single_segment()

        while req_segment.get_flag().get_flag_bytes() != int_to_bytes(SYN_FLAG):
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
        reply_segment.set_flag([SYN_FLAG, ACK_FLAG])
        print("[!] [Handshake] Waiting for response...")
        self.client_connection.send_data(reply_segment, ("localhost", self.broadcast_port))
        self.seq_number += 1

        # Tunggu ACK
        reply_segment = self.client_connection.listen_single_segment()

        while reply_segment.get_flag().get_flag_bytes() != int_to_bytes(ACK_FLAG):
            reply_segment = self.client_connection.listen_single_segment()

        print("[!] [Handshake] ACK reply received")
        return

    def listen_file_transfer(self):
        # File transfer, client-side
        file_segment = self.client_connection.listen_single_segment()

        with open(self.path_output, "wb") as out_file:
            while True:
                if (file_segment.get_flag().get_flag_bytes() == int_to_bytes(FIN_FLAG)):
                    # Penulisan selesai.
                    break
                
                # Lakukan penulisan
                out_file.write(file_segment.get_payload())

                # Dengarkan segment baru
                file_segment = self.client_connection.listen_single_segment()
        
        return


if __name__ == '__main__':
    if (len(sys.argv) != 4):
        print("[!] client.py could not start. Expected 3 arguments: [client port], [broadcast port], and [path file input].")
    else:
        main = Client()
        main.three_way_handshake()
        main.listen_file_transfer()
