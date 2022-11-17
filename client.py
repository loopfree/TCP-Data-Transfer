import sys
import time
import socket
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
        self.ack_number = None

        # Output required message
        print(f"[!] Client started at localhost:{self.client_port}")

        # Kirim request ke server
        request_message = Segment()
        request_message.set_payload(f'{self.client_port}'.encode())
        self.client_connection.send_data(request_message, ("localhost", self.broadcast_port))

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        '''
            How this works:
            (1) Server starts the three-way handshake
            (2) When listening for SYN and ACK segments, maximum timeout is 5 second. If timeout happens, restart handshake.
            (3) If three-way handshake takes longer than 500 seconds, mark process as failed.
        '''
        WAIT_TIME_LIMIT = 5         # 5 seconds
        HANDSHAKE_TIME_LIMIT = 300  # 300 seconds
        start_handshake_time = time.time()

        self.client_connection.set_listen_timeout(WAIT_TIME_LIMIT)

        req_header = None
        
        while True:
            # Check if timeout limit reached
            if time.time() - start_handshake_time > HANDSHAKE_TIME_LIMIT:
                print(f'[!] Could not establish connection with broadcast port {self.broadcast_port}. Stopping process ...')
                return False

            # Inisialisasi dimulai dari server, tunggu request.
            print("[!] [Three-Way Handshake] Waiting for SYN request...")
            try:
                req_segment = self.client_connection.listen_single_segment()
            except socket.timeout:
                print(f"[!] [Three-Way Handshake] Did not receive SYN segment, retrying ...")
                continue

            if (not req_segment.get_flag().is_syn_flag()):
                print(f"[!] [Three-Way Handshake] Wrong flag received. Expected SYN flag, retrying ...")
                continue

            req_header = req_segment.get_header()
            self.ack_number = req_header["seq_nb"] + 1
            print("[!] [Three-Way Handshake] SYN request received")

            break

        while True:
            # Kirim SYN-ACK
            print(f"[!] [Three-Way Handshake] Sending broadcast SYN-ACK reply to port {self.broadcast_port}")
            reply_segment = Segment()
            reply_segment.set_header({
                "seq_nb": self.seq_number,
                "ack_nb": req_header["seq_nb"] + 1
            })
            reply_segment.set_flag([SegmentFlag.SYN_FLAG, SegmentFlag.ACK_FLAG])
            self.client_connection.send_data(reply_segment, ("localhost", self.broadcast_port))

            # Tunggu ACK
            print("[!] [Three-Way Handshake] Waiting for response...")
            try:
                reply_segment = self.client_connection.listen_single_segment()
            except socket.timeout:
                print(f"[!] [Three-Way Handshake] Did not receive ACK segment, retrying ...")
                continue
            
            if (reply_segment.get_flag().is_ack_flag()):
                print("[!] [Three-Way Handshake] ACK reply received")
                self.seq_number = reply_segment.get_header()['ack_nb']
                break

            # Apabila belum menerima ACK tapi menerima file kiriman dari server, otomatis dilanjutkan ke proses file transfer
            elif (reply_segment.get_flag().is_null_flag()):
                print(f"[!] [Three-Way Handshake] File segment received instead. Commencing to file transfer ...")
                break
            
            else:
                print(f"[!] [Three-Way Handshake] Wrong flag received. Expecting ACK flag, retrying ...")
            
        return True

    def listen_file_transfer(self):
        # File transfer, client-side
        ack_nb = self.ack_number
        SEQ_TIMEOUT = 30
        last_recv_nb = ack_nb - 1
        last_recv_time = time.time()
        self.client_connection.set_listen_timeout(1)

        do_four_way_handshake = False

        with open(self.path_output, "wb") as out_file:
            while not do_four_way_handshake:
                try:
                    # Receive segment
                    file_segment = self.client_connection.listen_single_segment()
                    last_recv_time = time.time()

                    # Finish receiving file
                    if file_segment.get_flag().is_fin_flag():
                        do_four_way_handshake = True
                        break

                    # Check segment
                    if file_segment.get_flag().is_null_flag() and file_segment.get_header()["seq_nb"] == ack_nb and file_segment.valid_checksum():
                        out_file.write(file_segment.get_payload())
                        print(f"[!] [File Transfer] Written {len(file_segment.get_payload())} bytes")
                        print(f"[!] [File Transfer] Received segment {ack_nb}")
                        last_recv_nb = ack_nb
                        ack_nb += 1
                    else:
                        raise ValueError
                
                except ValueError:
                    print(f"[!] [File Transfer] Received corrupted data when expecting for segment {ack_nb}")
                except:
                    pass

                if last_recv_nb > 0:
                    # Send ACK
                    ack_segment = Segment()
                    ack_segment.set_header({"ack_nb": ack_nb})
                    ack_segment.set_flag([SegmentFlag.ACK_FLAG])
                    self.client_connection.send_data(ack_segment, ("localhost", self.broadcast_port))
                    print(f"[!] [File Transfer] Sending ACK {ack_nb} to server")
                
                # Force close connection on timeout
                if time.time() - last_recv_time > SEQ_TIMEOUT:
                    break

        if do_four_way_handshake:
            self.four_way_handshake(file_segment.get_header()['seq_nb'])

        return

    def four_way_handshake(self, fin_seq_nb):
        self.client_connection.set_listen_timeout(1)
        MAX_FWH_TIME = 5
        fwh_start = time.time()

        print("[!] [Four-Way Handshake] Handshake starting ...")
        while True:
            if time.time() - fwh_start > MAX_FWH_TIME:
                print("[!] [Four-Way Handshake] Timeout limit for four way handshake reached. Closing connection ...")
                break

            # Send ACK
            ack_sgmt = Segment()
            ack_sgmt.set_flag([SegmentFlag.ACK_FLAG])
            ack_sgmt.set_header({"ack_nb": fin_seq_nb + 1})
            self.client_connection.send_data(ack_sgmt, ("localhost", self.broadcast_port))
            print("[!] [Four-Way Handshake] ACK segment sent!")

            # Send FIN flag
            fin_sgmt = Segment()
            fin_sgmt.set_flag([SegmentFlag.FIN_FLAG])
            self.client_connection.send_data(fin_sgmt, ("localhost", self.broadcast_port))
            print("[!] [Four-Way Handshake] FIN segment sent!")

            # Wait for ACK flag
            try:
                ack_sgmt = self.client_connection.listen_single_segment()
                if ack_sgmt.get_flag().is_ack_flag():
                    print("[!] [Four-Way Handshake] ACK segment received!")
                else:
                    continue        # Restart sending ACK
            except socket.timeout:
                print("[!] [Four-Way Handshake] Timeout on no ACK received, closing client ...")
                break

if __name__ == '__main__':
    if (len(sys.argv) != 4):
        print("[!] client.py could not start. Expected 3 arguments: [client port], [broadcast port], and [path file input].")
    else:
        main = Client()
        if main.three_way_handshake():
            main.listen_file_transfer()
