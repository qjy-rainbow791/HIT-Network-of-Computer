import threading
from time import sleep
import gbn
import sr


def run_gbn(local: tuple[[str, int]],
            remote: tuple[[str, int]],
            window_num: int = 4,
            window_size: int = 1024):
    threading.Lock()
    host_1 = gbn.GBN(local, remote, window_num, window_size, 'h1')
    host_2 = gbn.GBN(remote, local, window_num, window_size, 'h2')
    server1 = threading.Thread(target=host_1.server_run, args=())
    server2 = threading.Thread(target=host_2.server_run, args=())
    server1.start()
    server2.start()
    while host_1.isHostAlive() or host_2.isHostAlive():
        sleep(0.2)
    host_1.shut_socket()
    host_2.shut_socket()


def run_sr(local: tuple[[str, int]],
           remote: tuple[[str, int]],
           window_num: int = 4,
           window_size: int = 1024):
    host_1 = sr.SR(local, remote, window_num, window_size)
    host_2 = sr.SR(remote, local, window_num, window_size)
    threading.Thread(target=host_1.server_run).start() 
    threading.Thread(target=host_2.client_run).start()
    while host_1.isHostAlive() or host_2.isHostAlive():
        sleep(0.2)
    host_1.shut_socket()
    host_2.shut_socket()


#print('gbn:\n')
#run_gbn(('127.0.0.1', 5000), ('127.0.0.1', 5001), 4, 10)
print('sr:\n')
run_sr(('127.0.0.1', 5000), ('127.0.0.1', 5001), 4, 10)
