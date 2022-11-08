import socket
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        # Init UDP socket
        # socket.AF_INET adalah familynya dan socket.SOCK_DGRAM adalah typenya
        self.udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_server_socket.bind((ip, port))
        pass

    def send_data(self, msg : Segment, dest : ("ip", "port")):
        # Send single segment into destination
        self.udp_server_socket.sendto(msg.get_bytes(), dest)
        pass

    def listen_single_segment(self) -> Segment:
        # Listen single UDP datagram within timeout and convert into segment
        return_segment = Segment()
        res = self.udp_server_socket.recvfrom(MAX_PAYLOAD_SIZE)
        return_segment.set_from_bytes(res[0])
        return return_segment

    def close_socket(self):
        # Release UDP socket
        self.udp_server_socket.shutdown(socket.SHUT_RDWR)
        self.udp_server_socket.close()
        pass
