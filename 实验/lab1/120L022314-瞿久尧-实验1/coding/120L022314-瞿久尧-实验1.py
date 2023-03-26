import json
import os
import socket
import threading
import time
import urllib.parse as urlparse

import requests


class ProxyServer(object):
    def __init__(self):
        self.severPort = 8080  # 代理服务器端口
        self.main_sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP主套接字
        self.main_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_sock.bind(('', self.severPort))  # 绑定端口
        self.MAX_LISTEN = 20
        self.main_sock.listen(self.MAX_LISTEN)  # 最大连接数
        self.HTTP_BUFFER_SIZE = 4096  # http缓存大小
        self.default_cache_dir = r'D:\Rainbow\Study\大三秋\计算机网络\实验\lab1\120L022314-瞿久尧-实验1\cache\\'
        self.making_cache_dir()

    def making_cache_dir(self):  # 缓存路径
        if not os.path.exists(self.default_cache_dir):
            os.mkdir(self.default_cache_dir)

    def filter_web(self, url):  # 过滤网站
        with open("config.json", "r") as f:
            filter_json = json.load(f)
            host_denied = filter_json['host']
            for url_denied in host_denied:
                if url in url_denied:
                    return True
            return False

    def filter_userip(self, ip):  # 过滤ip
        with open("config.json", "r") as f:
            filter_json = json.load(f)
            user_denied = filter_json['ip']
            if ip in user_denied:
                return True
            return False

    def filter_fishing(self, url):  # 钓鱼
        with open("config.json", "r") as f:
            filter_json = json.load(f)
            fishing = filter_json['fishing']
            for fishes in fishing:
                if url in fishes:
                    return True
            return False

    def proxy_connect(self, sock_to_web, address):
        message = sock_to_web.recv(
            self.HTTP_BUFFER_SIZE).decode('utf-8', 'ignore')

        print(f"Msg:{message}")
        msgs = message.split('\r\n')
        print(f"Format_msgs:{msgs}")
        request_line = msgs[0].strip().split()
        print(f"Request line:{request_line}")
        print(f"len(request line):{len(request_line)}")
        # print(f"request_line[1]:{request_line[1]}")
        if len(request_line) < 1:
            print("Request Line not contains url!")
            print(f"Full Request Message:{message}")
            sock_to_web.close()  # 关闭连接sock
            return

        else:
            # scheme://netloc/path;parameters?query#fragment url的一般形式 urlparse还可以包括 username password hostname port
            url = urlparse.urlparse(
                request_line[1][:-1] if request_line[1][-1] == '/' else request_line[1])
            print(f"url.scheme:{url.scheme},type:{type(url.scheme)}")
            print(f"url.hostname:{url.hostname},type:{type(url.hostname)}")
            print(f"url.port:{url.port},type:{type(url.port)}")
            print(f"url.scheme:{url.path},type:{type(url.path)}")
            print(f"url.netloc:{url.netloc},type:{type(url.netloc)}")

        if self.filter_web(url.hostname):  # 如果需要过滤某个网站
            with open("404.html") as f:
                sock_to_web.sendall(f.read().encode())
            sock_to_web.close()
            return

        
        #if self.filter_userip(address[0]):  # 如果需要过滤某个IP
        #    with open("403.html") as f:
        #        sock_to_web.sendall(f.read().encode())
        #    sock_to_web.close()
        #    return
        
        if self.filter_fishing(url.hostname):  # 将需要钓鱼的网站重定向至中国作家网
            sock_to_web.sendall(requests.get("http://www.chinawriter.com.cn/").content) #也可以尝试将钓鱼网站换成其他的，
            sock_to_web.close()
            return

        cache_path = self.default_cache_dir + \
            (str(url.hostname) + str(url.path)).replace('/', '_')
        flag_modified = False  # 默认缓存没有更改
        flag_exists = os.path.exists(cache_path)  # 检测缓存目录是否存在
        sock_to_Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if flag_exists:
            cache_time = os.stat(cache_path).st_mtime  # 获取缓存的时间
            msgs = {
                'If-Modified-Since': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(cache_time))}
            response = requests.get(url.geturl(), headers=msgs)
            if response.status_code == 304:  # 如果返回304 则无需进行重新访问
                print("Read From Cache" + cache_path)
                with open(cache_path, "rb") as f:
                    sock_to_web.sendall(f.read())
            else:
                flag_modified = True  # 否则证明缓存已经过时

        if not flag_exists or flag_modified:  # 如果没有缓存或者缓存文件已经发生变化
            print("Attempt to connect", url.geturl())
            sock_to_Client.connect(
                (url.hostname, url.port if url.port else 80))
            sock_to_Client.sendall(message.encode())
            temp_file = open(cache_path, 'w')  # 记录缓存
            while True:
                buff = sock_to_Client.recv(self.HTTP_BUFFER_SIZE)
                if not buff:
                    temp_file.close()
                    sock_to_Client.close()
                    break
                temp_file.write(buff.decode('gbk', 'ignore'))
                sock_to_web.sendall(buff)
            sock_to_web.close()


# 主函数 使用threading实现多线程
def main():
    proxy = ProxyServer()
    while True:
        new_sock, address = proxy.main_sock.accept()
        print(address)
        threading.Thread(target=proxy.proxy_connect,
                         args=(new_sock, address)).start()


# 程序入口
if __name__ == '__main__':
    main()
