import time
import random
import matplotlib.pyplot as plt
from network import TCPConnection, TCPPacket
import numpy as np

class TCPCubicConnection(TCPConnection):
    def __init__(self, name, rtt=0.15, max_packets=100, jitter=0.001, loss_rate=0.001):
        super().__init__(name, rtt, max_packets, jitter, loss_rate)
        self.cwnd = 1.0
        self.w_max = 0  # Window size before reduction
        self.w_last_max = 0  # Last Wmax for fast convergence
        self.k = 0  # Time period since last congestion
        self.t = 0  # Time since last congestion
        self.beta = 0.7  # CUBIC beta
        self.C = 0.4  # CUBIC scaling factor
        self.dupacks = 0
        self.time = 0
        self.times = []
        self.cwnds = []
        self.throughput = []
        self.bytes_sent = 0
        self.loss_events = []

    def cubic_update(self):
        # CUBIC window calculation
        self.t = (self.time - self.k)
        w_cubic = self.C * (self.t - self.k)**3 + self.w_max
        return max(w_cubic, 2)

    def send_data(self, data, peer):
        while self.sent_packets < self.max_packets:
            packets_to_send = int(self.cwnd)
            bytes_this_round = 0
            
            for _ in range(packets_to_send):
                packet = TCPPacket(seq=self.seq, data=data)
                self.send(packet, peer)
                self.seq += len(data)
                bytes_this_round += len(data)
            
            self.time += self.rtt
            self.bytes_sent += bytes_this_round
            current_throughput = self.bytes_sent / self.time
            
            # Record metrics
            self.times.append(self.time)
            self.cwnds.append(self.cwnd)
            self.throughput.append(current_throughput)
            
            if self._simulate_packet_loss():
                self._handle_loss()
            else:
                self._handle_success()

    def _simulate_packet_loss(self):
        return random.random() < self.loss_rate

    def _handle_loss(self):
        # Fast convergence
        if self.w_max < self.w_last_max:
            self.w_last_max = self.w_max
            self.w_max = self.w_max * (2 - self.beta) / 2
        else:
            self.w_last_max = self.w_max
            
        self.w_max = self.cwnd
        self.cwnd = self.cwnd * self.beta
        self.k = np.cbrt(self.w_max * (1 - self.beta) / self.C)
        self.loss_events.append(self.time)

    def _handle_success(self):
        self.cwnd = self.cubic_update()

    def plot_metrics(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot congestion window
        ax1.plot(self.times, self.cwnds)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Congestion Window (packets)')
        ax1.set_title('TCP CUBIC Congestion Window')
        
        for loss_time in self.loss_events:
            ax1.axvline(x=loss_time, color='red', alpha=0.3, linestyle='--')
            ax2.axvline(x=loss_time, color='red', alpha=0.3, linestyle='--')
        
        ax2.plot(self.times, self.throughput)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Throughput (bytes/s)')
        ax2.set_title('Network Throughput')
        
        ax1.plot([], [], color='red', linestyle='--', label='Packet Loss')
        ax1.legend()
        
        plt.tight_layout()
        plt.show()

def simulate_cubic():
    client = TCPCubicConnection('Client', rtt=0.15, loss_rate=0.02, max_packets=10000)
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
    simulate_cubic()