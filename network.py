import time
import random

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
    def __init__(self, name, rtt=0.15, max_packets=10000, jitter=0.001, loss_rate=0.001):
        self.name = name
        self.seq = 0
        self.ack = 0
        self.state = 'CLOSED'
        self.rtt = rtt
        self.max_packets = max_packets
        self.sent_packets = 0
        self.jitter = jitter
        self.loss_rate = loss_rate

    def send(self, packet, peer):
        if self.sent_packets >= self.max_packets:
            return
        if random.random() < self.loss_rate:
            print(f"{self.name}: Packet lost: {packet}")
            return
        print(f"{self.name} sending: {packet}")
        self.sent_packets += 1
        time.sleep(self.rtt + random.uniform(-self.jitter, self.jitter))
        peer.receive(packet, self)

    def receive(self, packet, peer):
        print(f"{self.name} received: {packet}")
        # Basic TCP state machine
        if packet.syn and not packet.ack_flag:
            self._handle_syn(packet, peer)
        elif packet.syn and packet.ack_flag:
            self._handle_synack(packet)
        elif packet.fin:
            self._handle_fin(packet, peer)
        elif packet.data:
            self._handle_data(packet, peer)

    def _handle_syn(self, packet, peer):
        self.ack = packet.seq + 1
        self.seq = 100
        syn_ack = TCPPacket(seq=self.seq, ack=self.ack, syn=True, ack_flag=True)
        self.state = 'SYN_RECEIVED'
        self.send(syn_ack, peer)

    def _handle_synack(self, packet):
        self.ack = packet.seq + 1
        self.state = 'ESTABLISHED'

    def _handle_fin(self, packet, peer):
        self.ack = packet.seq + 1
        fin_ack = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
        self.send(fin_ack, peer)

    def _handle_data(self, packet, peer):
        self.ack = packet.seq + len(packet.data)
        ack_packet = TCPPacket(seq=self.seq, ack=self.ack, ack_flag=True)
        self.send(ack_packet, peer)