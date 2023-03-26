import random
import select
import socket


class util:
    @staticmethod
    def mk_pkt(seqSen, seqRec, msg):
        return (str(seqSen) + ' ' + str(seqRec) + ' ' + str(msg)).encode('gb2312', 'ignore')

    @staticmethod
    def mk_pkt1(seq, msg):
        return (str(seq) + ' ' + str(msg)).encode('gb2312', 'ignore')


class GBN:

    def __init__(self,
                 local_address: tuple[[str, int]],
                 remote_address: tuple[[str, int]],
                 inputWindow_size: int = 4,
                 inputPkg_size: int = 1024,
                 hostNameInput: str = ''):

        self.hostname = hostNameInput
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
        self.read_path = 'file/gbn/' + self.hostname + '2read.txt'  # 需要发送的源文件数据
        self.ack_buf_size = 1678
        self.get_data_from_file()

        self.data_buf_size = 1678  # 作为客户端接收数据缓存
        self.exp_seq = 0  # 当前期望收到该序号的数据
        self.save_path = 'file/gbn/' + self.hostname + '2save.txt'  # 接收数据时，保存数据的地址
        self.write_data_to_file('', mode='w')

        self.pkt_loss = 0.1  # 发送数据丢包率
        self.ack_loss = 0.1  # 返回的ack丢包率
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.local_address)
        self.state_flag = 0

    def send_data(self):
        if self.send_base == len(self.data):  # data数据已全部发送并收到ack
            self.socket.sendto(util.mk_pkt(0, self.exp_seq - 1, 0), self.remote_address)
            print('服务器: ' + self.hostname + '\t' + '发送完毕!')
            return
        if self.next_seq == len(self.data):  # data数据已全部发送，无需发送
            return
        if self.next_seq - self.send_base < self.window_size:  # 窗口中仍有可用空间
            if random.random() > self.pkt_loss:  # 随机产生丢包行为
                self.socket.sendto(util.mk_pkt(self.next_seq, self.exp_seq - 1, self.data[self.next_seq]),
                                   self.remote_address)
                isLose = 0
            else:
                isLose = 1
            print('服务器: ' + self.hostname + '\t' + '成功发送数据: ' + str(self.next_seq)
                  + ' ack=' + str(self.exp_seq - 1), end='\n')
            if isLose == 1:
                print('服务器: ' + self.hostname + '\t' + '丢失数据包: ' + str(self.next_seq))
            self.next_seq = self.next_seq + 1
        else:  # 窗口中无可用空间
            print('服务器: ' + self.hostname + '\t' + '窗口已满，暂不发送数据', end='\n')

    # 超时处理函数：计时器置0
    def handle_time_out(self):
        print('服务器: ' + self.hostname + '\t' + '数据包: ' + str(self.send_base) + '超时，开始重传!', end='\n')
        self.time_count = 0  # 超时计次重启
        for i in range(self.send_base, self.next_seq):  # 发送空中的所有分组
            if random.random() > self.pkt_loss:  # 概率性重传
                self.socket.sendto(util.mk_pkt(i, self.exp_seq - 1, self.data[i]), self.remote_address)
                isLose = 0
            else:
                isLose = 1
            print('服务器: ' + self.hostname + '\t' + '数据: ' + str(i)
                  + ' ack=' + str(self.exp_seq - 1) + '已重发!', end='\n')
            if isLose == 1:
                print('服务器: ' + self.hostname + '\t' + '丢失数据包: ' + str(i), end='\n')

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
        rcv_finish = 0
        send_finish = 0
        while True:
            self.send_data()  # 发送数据逻辑
            readable = select.select([self.socket], [], [], 1)[0]
            if len(readable) > 0:  # 接收到数据
                rcv_data = self.socket.recvfrom(self.data_buf_size)[0].decode('gb2312')
                rcv_seq = rcv_data.split()[0]  # 按照格式规约获取数据序号
                rcv_ack = rcv_data.split()[1]
                rcv_data = rcv_data.replace(rcv_seq + ' ' + rcv_ack + ' ', '')  # 按照格式规约获取数据
                print('服务器: ' + self.hostname + '\t' + '接收到数据: ' + rcv_seq + ' ack: ' + rcv_ack, end='\n')
                if int(rcv_seq) == self.exp_seq:  # 接收到按序数据包
                    print('服务器: ' + self.hostname + '\t' + '接收到期望序号数据: ' + rcv_seq, end='\n')
                    self.write_data_to_file(rcv_data)  # 保存服务器端发送的数据到本地文件中
                    self.exp_seq = self.exp_seq + 1  # 期望数据的序号更新
                elif rcv_seq == '0' and rcv_data == '0':  # 接收到结束包
                    print('服务器: ' + self.hostname + '\t' + '接收数据结束', end='\n')
                    rcv_finish = 1
                else:
                    print('服务器: ' + self.hostname + '\t' + '接收到非期望数据，期望: ' +
                          str(self.exp_seq) + '实际:' + str(rcv_seq), end='\n')
                if int(rcv_ack) < self.send_base:
                    self.time_count += 1
                else:
                    self.send_base = int(rcv_ack) + 1  # 滑动窗口的起始序号
                    self.time_count = 0
                print('服务器: ' + self.hostname + '\t' + 'self.send_base=' + str(self.send_base), end='\n')
            else:  # 未收到包
                self.time_count += 1  # 超时计次+1
            if self.time_count > self.time_out:  # 触发超时重传操作
                self.handle_time_out()
            if self.send_base == len(self.data):  # 判断数据是否传输结束
                self.socket.sendto(util.mk_pkt(0, self.exp_seq - 1, 0), self.remote_address)  # 发送结束报文
                print('服务器: ' + self.hostname + '\t' + '发送完毕', end='\n')
                send_finish = 1
            if rcv_finish == 1 and send_finish == 1:
                print('服务器: ' + self.hostname + '\t' + '发送接收均完毕!!', end='\n')
                break
        self.state_flag = 0

    # 保存来自服务器的合适的数据
    def write_data_to_file(self, data, mode='a'):
        with open(self.save_path, mode, encoding='gb2312') as f:
            f.write(data)  # 模拟将数据交付到上层

    def isHostAlive(self):
        return self.state_flag

    def shut_socket(self):
        self.socket.close()
