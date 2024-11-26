from frame import SlidingWindowTCPConnection, TCPPacket

class RenoTCPConnection(SlidingWindowTCPConnection):
    def __init__(self, name, router, rtt=0.005, max_packets=10000, jitter=0.001, loss_rate=0.001, timeout=1, window_size=5):
        super().__init__(name, router, rtt, max_packets, jitter, loss_rate, timeout, window_size)
        self.cwnd = 1  # 拥塞窗口大小
        self.ssthresh = 16  # 慢启动阈值
        self.dup_ack_count = 0  # 重复ACK计数
        self.last_ack = 0  # 上一个ACK
        self.cwnd_history = []  # 存储拥塞窗口大小的历史记录
        self.cwnd_history.append(self.cwnd)  # 初始化记录

    async def receive(self, packet, peer):
        # ...existing code...
        await super().receive(packet, peer)
        if packet.ack_flag:
            if packet.ack > self.last_ack:
                # 新的ACK，进入拥塞避免
                self.dup_ack_count = 0
                if self.cwnd < self.ssthresh:
                    # 慢启动阶段
                    self.cwnd += 1
                else:
                    # 拥塞避免阶段
                    self.cwnd += 1 / self.cwnd
                self.cwnd_history.append(self.cwnd)  # 记录cwnd变化
                self.last_ack = packet.ack
            elif packet.ack == self.last_ack:
                # 重复ACK
                self.dup_ack_count += 1
                if self.dup_ack_count == 3:
                    # 三次重复ACK，进行快速重传
                    self.ssthresh = max(self.cwnd / 2, 1)
                    self.cwnd = self.ssthresh + 3
                    self.cwnd_history.append(self.cwnd)  # 记录cwnd变化
                    # 重传丢失的数据包
                    lost_packet = self.sent_packets_dict.get(packet.ack - 1)
                    if lost_packet:
                        await self.send(lost_packet, peer)
            # 调整发送窗口
            while self.buffer and self.next_seq < self.base + int(self.cwnd):
                _, pkt = self.buffer.popitem(last=False)
                await self.send(pkt, peer)

