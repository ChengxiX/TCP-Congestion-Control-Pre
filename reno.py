import time
import random
import matplotlib.pyplot as plt
from network import TCPConnection, TCPPacket

class TCPRenoConnection(TCPConnection):
    def __init__(self, name, rtt=0.15, max_packets=100, jitter=0.001, loss_rate=0.001):
        super().__init__(name, rtt, max_packets, jitter, loss_rate)
        self.cwnd = 1.0
        self.ssthresh = 64
        self.dupacks = 0
        self.time = 0
        self.times = []
        self.cwnds = []
        self.throughput = []
        self.bytes_sent = 0

    def send_data(self, data, peer):
        start_time = time.time()
        while self.sent_packets < self.max_packets:
            packets_to_send = int(self.cwnd)
            bytes_this_round = 0
            
            for _ in range(packets_to_send):
                packet = TCPPacket(seq=self.seq, data=data)
                self.send(packet, peer)
                self.seq += len(data)
                bytes_this_round += len(data)
            
            # Simulate network delay
            time.sleep(self.rtt)
            
            # Update metrics
            self.time += self.rtt
            self.bytes_sent += bytes_this_round
            current_throughput = self.bytes_sent / self.time
            
            # Record metrics
            self.times.append(self.time)
            self.cwnds.append(self.cwnd)
            self.throughput.append(current_throughput)
            
            # TCP Reno congestion control
            if self._simulate_packet_loss():
                self._handle_loss()
            else:
                self._handle_success()

    def _simulate_packet_loss(self):
        return random.random() < self.loss_rate

    def _handle_loss(self):
        self.ssthresh = max(self.cwnd / 2, 2)
        self.cwnd = 1
        self.dupacks = 0

    def _handle_success(self):
        if self.cwnd < self.ssthresh:
            # Slow start
            self.cwnd *= 2
        else:
            # Congestion avoidance
            self.cwnd += 1.0 / self.cwnd

    def plot_metrics(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot congestion window
        ax1.plot(self.times, self.cwnds)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Congestion Window (packets)')
        ax1.set_title('TCP Reno Congestion Window')
        
        # Plot throughput
        ax2.plot(self.times, self.throughput)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Throughput (bytes/s)')
        ax2.set_title('Network Throughput')
        
        plt.tight_layout()
        plt.show()

def simulate_reno():
    client = TCPRenoConnection('Client')
    server = TCPConnection('Server')
    
    # Establish connection
    syn = TCPPacket(seq=0, syn=True)
    client.send(syn, server)
    
    # Send data
    data = "X" * 1000  # 1KB of data
    client.send_data(data, server)
    
    # Plot results
    client.plot_metrics()

if __name__ == "__main__":
    simulate_reno()