import time
import random
import asyncio
from collections import OrderedDict

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
        if self.syn: flags.append('SYN')
        if self.ack_flag: flags.append('ACK')
        if self.fin: flags.append('FIN')
        flag_str = '|'.join(flags) if flags else 'NONE'
        return f"SEQ={self.seq}, ACK={self.ack}, FLAGS={flag_str}, DATA={self.data}"

class TCPConnection:
    def __init__(self, name, router, rtt=0.005, max_packets=10000, jitter=0.001, loss_rate=0.001):
        self.name = name
        self.seq = 0
        self.ack = 0
        self.state = 'CLOSED'
        self.rtt = rtt
        self.max_packets = max_packets
        self.sent_packets = 0
        self.jitter = jitter
        self.loss_rate = loss_rate
        self.router = router

    async def send(self, packet, peer):
        if self.sent_packets >= self.max_packets:
            return
        if random.random() < self.loss_rate:
            # print(f"{self.name}: Packet lost;")
            return
        # print(f"{self.name} sending;")
        self.sent_packets += 1
        # 模拟发送延迟
        await asyncio.sleep(self.rtt + random.uniform(-self.jitter, self.jitter))
        # 修改为通过Router发送
        await self.router.forward(packet, self, peer)

    async def receive(self, packet, peer):
        if packet.syn and not packet.ack_flag:
            await self._handle_syn(packet, peer)
        elif packet.syn and packet.ack_flag:
            await self._handle_synack(packet)
        elif packet.fin:
            await self._handle_fin(packet, peer)
        elif packet.data:
            await self._handle_data(packet, peer)

    async def _handle_syn(self, packet, peer):
        self.ack = packet.seq + 1
        self.seq = 100
        syn_ack = TCPPacket(seq=self.seq, ack=self.ack, syn=True, ack_flag=True)
        self.state = 'SYN_RECEIVED'
        await self.send(syn_ack, peer)

    async def _handle_synack(self, packet):
        self.ack = packet.seq + 1
        self.state = 'ESTABLISHED'

    async def _handle_fin(self, packet, peer):
        self.ack = packet.seq + 1
        fin_ack = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
        await self.send(fin_ack, peer)

    async def _handle_data(self, packet, peer):
        self.ack = packet.seq + len(packet.data)
        ack_packet = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
        self.handle(packet.data)
        await self.send(ack_packet, peer)

    def handle(self, data):
        print(f"{self.name} received: {data}")

class TCPConnectionWithTimeout(TCPConnection):
    def __init__(self, name, router, rtt=0.005, max_packets=10000, jitter=0.001, loss_rate=0.001, timeout=1):
        super().__init__(name, router, rtt, max_packets, jitter, loss_rate)
        self.received_acks = set()  # 跟踪已接收的 ACK 序列号
        self.timeout = timeout

    async def send(self, packet, peer):
        # 调用父类的 send 方法
        await super().send(packet, peer)
        # 启动超时重传任务
        asyncio.create_task(self._timeout(packet, peer, self.timeout))

    async def receive(self, packet, peer):
        # 调用父类的 receive 方法
        await super().receive(packet, peer)
        if packet.ack_flag:
            self.received_acks.add(packet.ack)

    async def _timeout(self, packet, peer, _timeout=1):
        await asyncio.sleep(_timeout)  # 设置超时时间
        if not self.is_ack_received(packet.seq):
            # 超时未收到 ACK，重传包
            await self.send(packet, peer)

    def is_ack_received(self, seq):
        # 检查是否收到对应序列号的 ACK
        return (seq + 1 in self.received_acks)

class SlidingWindowTCPConnection(TCPConnectionWithTimeout):
    def __init__(self, name, router, rtt=0.005, max_packets=10000, jitter=0.001, loss_rate=0.001, timeout=1, window_size=5):
        super().__init__(name, router, rtt, max_packets, jitter, loss_rate, timeout)
        self.window_size = window_size  # 窗口大小
        self.base = 1  # 窗口起始序号，从1开始
        self.next_seq = 0  # 下一个发送的序号
        self.buffer = OrderedDict()  # 使用有序字典作为待发送的数据包队列
        self.sent_packets_dict = {}  # 已发送但未确认的数据包 {seq: packet}
    
    async def send(self, packet, peer):
        if self.next_seq < self.base + self.window_size and self.sent_packets_dict.get(packet.seq) is None:
            # 在窗口范围内且未发送过该包，发送包
            await super().send(packet, peer)
            self.sent_packets_dict[packet.seq] = packet
            asyncio.create_task(self._timeout(packet, peer, self.timeout))
            self.next_seq += 1
        else:
            # 窗口已满，将包加入缓冲队列，确保不重复
            if packet.seq not in self.buffer:
                self.buffer[packet.seq] = packet
    
    async def receive(self, packet, peer):
        # ...existing code...
        await super().receive(packet, peer)
        if packet.ack_flag:
            if packet.ack > self.base:
                self.base = packet.ack
                # 移除已确认的包
                for seq in list(self.sent_packets_dict):
                    if seq < self.base:
                        del self.sent_packets_dict[seq]
                # 发送缓冲队列中的数据包
                while self.buffer and self.next_seq < self.base + self.window_size:
                    _, pkt = self.buffer.popitem(last=False)
                    await self.send(pkt, peer)
    
    # ...existing code...

class Router:
    def __init__(self, send_interval=0.001, max_buffer_size=100):
        self.buffer = []  # 使用列表作为缓存
        self.max_buffer_size = max_buffer_size
        self.send_interval = send_interval
        # 启动发送任务
        asyncio.create_task(self.send_packets())

    async def forward(self, packet, sender, receiver):
        if len(self.buffer) >= self.max_buffer_size:
            # 缓存已满，丢弃数据包
            return
        # 将包添加到缓存队列
        self.buffer.append((packet, sender, receiver))

    async def send_packets(self):
        while True:
            if self.buffer:
                # 从列表中取出第一个包并发送
                packet, sender, receiver = self.buffer.pop(0)
                # 创建任务处理发送延迟和接收
                asyncio.create_task(self._deliver_packet(packet, sender, receiver))
            await asyncio.sleep(self.send_interval)
    
    async def _deliver_packet(self, packet, sender, receiver):
        # 模拟发送延迟
        await asyncio.sleep(receiver.rtt + random.uniform(-receiver.jitter, receiver.jitter))
        await receiver.receive(packet, sender)

