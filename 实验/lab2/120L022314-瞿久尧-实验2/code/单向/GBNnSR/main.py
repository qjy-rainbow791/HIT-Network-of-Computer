import threading
from time import sleep
import gbn


def run_gbn(local: tuple[[str, int]],
            remote: tuple[[str, int]],
            window_num: int = 4,
            window_size: int = 1024):
    threading.Lock()
    host_1 = gbn.GBN(local, remote, window_num, window_size)
    host_2 = gbn.GBN(remote, local, window_num, window_size)
    client = threading.Thread(target=host_1.client_run, args=())
    server = threading.Thread(target=host_2.server_run, args=())
    server.start()
    client.start()
    while host_1.isHostAlive() or host_2.isHostAlive():
        sleep(0.2)
    host_1.shut_socket()
    host_2.shut_socket()


#print('停等协议:\n')
#run_gbn(('127.0.0.1', 5000), ('127.0.0.1', 5001), 1, 10)
print('gbn:\n')
run_gbn(('127.0.0.1', 5000), ('127.0.0.1', 5001), 4, 10)
