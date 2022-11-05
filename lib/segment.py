import struct

# Constants 
SYN_FLAG = 0b01000000
ACK_FLAG = 0b00001000
FIN_FLAG = 0b10000000

class SegmentFlag:
    def __init__(self, flag : bytes):
        # Init flag variable from flag byte
        self.flag = flag

    def get_flag_bytes(self) -> bytes:
        # Convert this object to flag in byte form
        return self.flag


class Segment:
    # -- Internal Function --
    def __init__(self):
        # Initalize segment
        self.seq_nb = 0
        self.ack_nb = 0
        self.flag = SegmentFlag(b'\x00')
        self.checksum = 0
        self.payload = b''

    def __str__(self):
        # Optional, override this method for easier print(segmentA)
        output = ""
        output += f"{'Sequence number':24} | {self.seq_nb}\n"
        return output

    def __calculate_checksum(self) -> int:
        # Checksum calculation with Internet Checksum
        pass


    # -- Setter --
    def set_header(self, header : dict):
        self.seq_nb = header['seq_nb']
        self.ack_nb = header['ack_nb']

    def set_payload(self, payload : bytes):
        self.payload = payload

    def set_flag(self, flag_list : list):
        self.flag = SegmentFlag(sum(flag_list).to_bytes(1, byteorder='big'))


    # -- Getter --
    def get_flag(self) -> SegmentFlag:
        return self.flag

    def get_header(self) -> dict:
        return {'seq_nb': self.seq_nb,
                'ack_nb': self.ack_nb}

    def get_payload(self) -> bytes:
        return self.payload


    # -- Marshalling --
    def set_from_bytes(self, src : bytes):
        # From pure bytes, unpack() and set into python variable
        self.seq_nb, self.ack_nb, flag_byte, self.checksum, self.payload = struct.unpack('!IIsxH32756s', src)
        self.flag = SegmentFlag(flag_byte)

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        return struct.pack('!IIsxH32756s', self.seq_nb, self.ack_nb, self.flag.get_flag_bytes(),
                                           self.checksum, self.payload)


    # -- Checksum --
    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        pass
