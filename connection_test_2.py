from lib.connection import Connection, Segment

conn_2 = Connection("127.0.0.1", 10000)

while (True):
    res = conn_2.listen_single_segment()
    message = res.get_payload()
    print(message)
