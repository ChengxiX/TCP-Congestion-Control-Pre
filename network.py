import time

class TCPPacket:
    def __init__(self, seq=0, ack=0, syn=False, ack_flag=False, fin=False, data=''):
        self.seq = seq
        self.ack = ack
        self.syn = syn
        self.ack_flag = ack_flag
        self.fin = fin
        self.data = data

    def __str__(self):
        flags = []
        if self.syn:
            flags.append('SYN')
        if self.ack_flag:
            flags.append('ACK')
        if self.fin:
            flags.append('FIN')
        flag_str = '|'.join(flags) if flags else 'NONE'
        return f"SEQ={self.seq}, ACK={self.ack}, FLAGS={flag_str}, DATA={self.data}"

class TCPConnection:
    def __init__(self, name, rtt=0.15, max_packets=10000):
        self.name = name
        self.seq = 0
        self.ack = 0
        self.state = 'CLOSED'
        self.rtt = rtt
        self.max_packets = max_packets
        self.sent_packets = 0

    def send(self, packet, peer):
        if self.sent_packets >= self.max_packets:
            print(f"{self.name}：已达到最大发送包数量，停止发送")
            return
        print(f"{self.name} 发送包: {packet}")
        self.sent_packets += 1
        time.sleep(self.rtt)  # 模拟RTT延迟
        peer.receive(packet, self)

    def receive(self, packet, peer):
        print(f"{self.name} 接收包: {packet}")
        if packet.syn and not packet.ack_flag:
            self.ack = packet.seq + 1
            self.seq = 100  # 初始序列号
            syn_ack = TCPPacket(seq=self.seq, ack=self.ack, syn=True, ack_flag=True)
            self.state = 'SYN_RECEIVED'
            self.send(syn_ack, peer)
        elif packet.syn and packet.ack_flag:
            self.ack = packet.seq + 1
            self.state = 'ESTABLISHED'
            print(f"{self.name}：连接已建立")
        elif packet.ack_flag and self.state == 'SYN_SENT':
            self.state = 'ESTABLISHED'
            print(f"{self.name}：连接已建立")
        elif packet.fin:
            self.ack = packet.seq + 1
            fin_ack = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
            self.state = 'CLOSE_WAIT'
            self.send(fin_ack, peer)
            fin_packet = TCPPacket(seq=self.seq, ack=self.ack, fin=True)
            self.state = 'LAST_ACK'
            self.send(fin_packet, peer)
        elif packet.ack_flag and self.state == 'FIN_WAIT_1':
            self.state = 'FIN_WAIT_2'
        elif packet.fin and self.state == 'FIN_WAIT_2':
            self.ack = packet.seq + 1
            ack_packet = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
            self.state = 'TIME_WAIT'
            self.send(ack_packet, peer)
            print(f"{self.name}：连接已关闭")
        elif packet.data:
            self.ack = packet.seq + len(packet.data)
            ack_packet = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
            print(f"{self.name}：收到数据 - {packet.data}")
            self.send(ack_packet, peer)

def simulate_tcp_connection():
    client = TCPConnection('客户端', rtt=0.15, max_packets=10000)
    server = TCPConnection('服务器', rtt=0.15, max_packets=10000)

    # 三次握手
    client.seq = 0
    syn_packet = TCPPacket(seq=client.seq, syn=True)
    client.state = 'SYN_SENT'
    client.send(syn_packet, server)

    # 数据传输
    if client.state == 'ESTABLISHED' and server.state == 'ESTABLISHED':
        data_packet = TCPPacket(seq=client.seq, ack=client.ack, data="Hello, Server!")
        client.send(data_packet, server)

    # 四次挥手
    fin_packet = TCPPacket(seq=client.seq, ack=client.ack, fin=True)
    client.state = 'FIN_WAIT_1'
    client.send(fin_packet, server)

simulate_tcp_connection()