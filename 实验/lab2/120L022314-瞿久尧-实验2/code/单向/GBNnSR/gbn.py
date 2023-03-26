import random
import select
import socket


class util:
    @staticmethod
    def mk_pkt(seq, msg):
        return (str(seq) + ' ' + str(msg)).encode('gb2312', 'ignore')


class GBN:

    def __init__(self,
                 local_address: tuple[[str, int]],
                 remote_address: tuple[[str, int]],
                 inputWindow_size: int = 4,
                 inputPkg_size: int = 1024):

        self.fin_flag = 0
        self.pkg_size = inputPkg_size  # 单格窗口大小
        self.window_size = inputWindow_size  # 窗口尺寸
        self.send_base = 0  # 发送窗口的最左序号
        self.next_seq = 0  # 当前未被利用的序号
        self.time_count = 0  # 记录当前传输时间
        self.time_out = 5  # 设置超时时间
        self.local_address = local_address  # 设置本地socket地址
        self.remote_address = remote_address  # 设置远程socket地址
        self.data = []  # 缓存发送数据
        self.read_path = 'file/gbn/2read.txt'  # 需要发送的源文件数据
        self.ack_buf_size = 10
        self.get_data_from_file()

        self.data_buf_size = 1678  # 作为客户端接收数据缓存
        self.exp_seq = 0  # 当前期望收到该序号的数据
        self.save_path = 'file/gbn/2save.txt'  # 接收数据时，保存数据的地址
        self.write_data_to_file('', mode='w')

        self.pkt_loss = 0.1  # 发送数据丢包率
        self.ack_loss = 0.1  # 返回的ack丢包率
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.local_address)
        self.state_flag = 0

    def send_data(self):
        if self.next_seq == len(self.data):  # data数据已全部被发送过
            print('服务器:发送完毕，等待确认')
            return
        if self.next_seq - self.send_base < self.window_size:  # 窗口中仍有可用空间
            if random.random() > self.pkt_loss:  # 随机产生丢包行为
                self.socket.sendto(util.mk_pkt(self.next_seq, self.data[self.next_seq]),
                                   self.remote_address)
            else:
                print('数据包' + str(self.next_seq) + '丢失')
            print('服务器:成功发送数据' + str(self.next_seq), end='\n')
            self.next_seq = self.next_seq + 1
        else:  # 窗口中无可用空间
            print('服务器：窗口已满，暂不发送数据', end='\n')

    # 超时处理函数：计时器置0
    def handle_time_out(self):
        print('超时，开始重传', end='\n')
        self.time_count = 0  # 超时计次重启
        for i in range(self.send_base, self.next_seq):  # 发送空中的所有分组
            if random.random() > self.pkt_loss:  # 概率性重传
                self.socket.sendto(util.mk_pkt(i, self.data[i]), self.remote_address)
            print('数据已重发:' + str(i), end='\n')

    # 从文本中读取数据用于模拟上层协议数据的到来
    def get_data_from_file(self):
        f = open(self.read_path, 'r', encoding='gb2312')
        while True:
            send_data = f.read(self.pkg_size)
            if len(send_data) <= 0:
                break
            self.data.append(send_data)  # 将读取到的数据保存到data数据结构中

    # 线程执行函数，不断发送数据并接收ACK报文做相应的处理
    def server_run(self):
        self.state_flag = 1
        while True:
            self.send_data()  # 发送数据逻辑
            readable = select.select([self.socket], [], [], 1)[0]
            if len(readable) > 0:  # 接收ACK数据
                rcv_ack = self.socket.recvfrom(self.ack_buf_size)[0].decode('gb2312').split()[0]
                print('收到客户端ACK:' + rcv_ack + '', end='\n')
                self.send_base = int(rcv_ack) + 1  # 滑动窗口的起始序号
                self.time_count = 0  # 计时器计次清0
            else:  # 未收到ACK包
                self.time_count += 1  # 超时计次+1
                if self.time_count > self.time_out:  # 触发超时重传操作
                    self.handle_time_out()
            if self.send_base == len(self.data):  # 判断数据是否传输结束
                self.socket.sendto(util.mk_pkt(0, 0), self.remote_address)  # 发送结束报文
                print('服务器:发送完毕', end='\n')
                break
        self.state_flag = 0

    # 保存来自服务器的合适的数据
    def write_data_to_file(self, data, mode='a'):
        with open(self.save_path, mode, encoding='gb2312') as f:
            f.write(data)  # 模拟将数据交付到上层

    # 主要执行函数，不断接收服务器发送的数据，若为期待序号的数据，则保存到本地，否则直接丢弃；并返回相应的ACK报文
    def client_run(self):
        self.fin_flag = 1
        while True:
            readable = select.select([self.socket], [], [], 1)[0]  # 非阻塞接收
            if len(readable) > 0:  # 接收到数据
                rcv_data = self.socket.recvfrom(self.data_buf_size)[0].decode('gb2312')
                rcv_seq = rcv_data.split()[0]  # 按照格式规约获取数据序号
                rcv_data = rcv_data.replace(rcv_seq + ' ', '')  # 按照格式规约获取数据
                if int(rcv_seq) == self.exp_seq:  # 接收到按序数据包
                    print('客户端:收到期望序号数据:' + str(rcv_seq), end='\n')
                    self.write_data_to_file(rcv_data)  # 保存服务器端发送的数据到本地文件中
                    self.exp_seq = self.exp_seq + 1  # 期望数据的序号更新
                else:
                    print('客户端:收到非期望数据，期望:' + str(self.exp_seq) + '实际:' + str(rcv_seq), end='\n')
                if rcv_seq == '0' and rcv_data == '0':  # 接收到结束包
                    print('客户端:传输数据结束', end='\n')
                    break
                print('客户端：发送ACK' + str(self.exp_seq - 1), end='\n')
                if random.random() >= self.ack_loss:  # 随机丢包发送数据
                    self.socket.sendto(util.mk_pkt(self.exp_seq - 1, 0), self.remote_address)
                else:
                    print('ACK' + str(self.exp_seq - 1) + '发送失败')
        self.fin_flag = 0

    def isHostAlive(self):
        return self.state_flag

    def shut_socket(self):
        self.socket.close()
