import struct

# Constants 
SYN_FLAG = 0b01000000
ACK_FLAG = 0b00001000
FIN_FLAG = 0b10000000
MAX_PAYLOAD_SIZE = 32756

# -- Utility Function --
def add_one_complement(m : int, n : int, size : int) -> int:
    # m and n is size-bit integer
    sum = m + n
    max_val = 1 << size
    if sum < max_val:
        return sum
    else:
        # Guarantee: (m + n) < (2 * 2^size)
        return (sum + 1) % max_val


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
        self.payload = b''
        self.payload_size = 0
        self.checksum = 0
        self.checksum = self.__calculate_checksum()

    def __str__(self):
        output = ""
        output += f"{'Sequence number':24} | {self.seq_nb}\n"
        return output

    def __calculate_checksum(self) -> int:
        # Checksum calculation with Internet Checksum (16-bit)
        # against the whole segment
        segment_bytes = self.get_bytes()
        checksum = 0

        for i in range(0, len(segment_bytes), 2):
            checksum = add_one_complement(checksum, int.from_bytes(segment_bytes[i:i+2], byteorder='big'), size=16)
        
        checksum = ~checksum + (1 << 16)
        return checksum

    # -- Setter --
    def set_header(self, header : dict):
        self.seq_nb = header['seq_nb']
        self.ack_nb = header['ack_nb']
        self.checksum = 0
        self.checksum = self.__calculate_checksum()

    def set_payload(self, payload : bytes):
        self.payload = payload
        self.payload_size = len(payload)
        self.checksum = 0
        self.checksum = self.__calculate_checksum()

    def set_flag(self, flag_list : list):
        self.flag = SegmentFlag(sum(flag_list).to_bytes(1, byteorder='big'))
        self.checksum = 0
        self.checksum = self.__calculate_checksum()


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
        self.payload_size = len(src) - 12
        self.seq_nb, self.ack_nb, flag_byte, self.checksum, self.payload = struct.unpack(f'!IIsxH{self.payload_size}s', src)
        self.flag = SegmentFlag(flag_byte)

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        return struct.pack(f'!IIsxH{self.payload_size}s', self.seq_nb, self.ack_nb, self.flag.get_flag_bytes(),
                                                          self.checksum, self.payload)


    # -- Checksum --
    def valid_checksum(self) -> bool:
        # Check integrity of this object
        return self.__calculate_checksum() == 0x0000
