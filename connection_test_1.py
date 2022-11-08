from lib.connection import Connection, Segment

conn_1 = Connection("127.0.0.1", 6969)

while (True):
    message = input("Masukkan pesan yang ingin dikirimkan: ")

    sent_segment = Segment()
    sent_segment.set_payload(message.encode())

    conn_1.send_data(sent_segment, ("127.0.0.1", 10000))

