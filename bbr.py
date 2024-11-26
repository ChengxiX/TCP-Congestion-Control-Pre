import time
import random
import matplotlib.pyplot as plt
from network import TCPConnection, TCPPacket
from enum import Enum

class BBRState(Enum):
    STARTUP = 1
    DRAIN = 2
    PROBE_BW = 3
    PROBE_RTT = 4

class TCPBBRConnection(TCPConnection):
    def __init__(self, name, rtt=0.15, max_packets=100, jitter=0.001, loss_rate=0.001):
        super().__init__(name, rtt, max_packets, jitter, loss_rate)
        # BBR state variables
        self.state = BBRState.STARTUP
        self.min_rtt = float('inf')
        self.max_bw = 0.0
        self.round_count = 0
        self.next_send_time = 0
        self.pacing_rate = float('inf')
        self.max_pacing_rate = 1000000  # 1M packets per second as a reasonable limit
        self.cwnd = 10.0  # Initial window
        self.probe_rtt_done_stamp = 0
        self.probe_rtt_min_stamp = 0
        self.min_rtt_stamp = 0
        
        # Metrics for plotting
        self.time = 0
        self.times = []
        self.cwnds = []
        self.bw_estimates = []
        self.rtt_estimates = []
        self.states = []
        self.bytes_sent = 0
        self.throughput = []

    def send_data(self, data, peer):
        while self.sent_packets < self.max_packets:
            current_time = self.time
            
            self._update_bbr_state(current_time)
            
            # Add bounds checking for pacing_rate calculation
            effective_pacing_rate = min(self.pacing_rate, self.max_pacing_rate)
            max_packets_by_rate = max(1, min(1000, int(effective_pacing_rate * self.rtt)))
            
            # Calculate packets to send with bounds
            packets_to_send = min(
                int(self.cwnd),
                max_packets_by_rate,
                self.max_packets - self.sent_packets
            )
            
            bytes_this_round = 0
            
            for _ in range(packets_to_send):
                if current_time >= self.next_send_time:
                    packet = TCPPacket(seq=self.seq, data=data)
                    self.send(packet, peer)
                    self.seq += len(data)
                    bytes_this_round += len(data)
                    self.next_send_time = current_time + (1.0 / effective_pacing_rate)
            
            self.time += self.rtt
            self.bytes_sent += bytes_this_round
            
            self._record_metrics()
            
            if self._simulate_packet_loss():
                self._update_bandwidth_rtt(lost=True)
            else:
                self._update_bandwidth_rtt()

    def _simulate_packet_loss(self):
        return random.random() < self.loss_rate

    def _update_bbr_state(self, current_time):
        if self.state == BBRState.STARTUP:
            if self.max_bw > 0 and self._bw_decreased():
                self.state = BBRState.DRAIN
        
        elif self.state == BBRState.DRAIN:
            if self._inflight() <= self._bdp():
                self.state = BBRState.PROBE_BW
        
        elif self.state == BBRState.PROBE_BW:
            if current_time - self.min_rtt_stamp > 10:
                self.state = BBRState.PROBE_RTT
        
        elif self.state == BBRState.PROBE_RTT:
            if current_time - self.probe_rtt_done_stamp > self.min_rtt:
                self.state = BBRState.PROBE_BW

        self._update_pacing_rate()

    def _update_pacing_rate(self):
        if self.state == BBRState.STARTUP:
            self.pacing_rate = min(2 * self.max_bw, self.max_pacing_rate)
        elif self.state == BBRState.DRAIN:
            self.pacing_rate = min(self.max_bw, self.max_pacing_rate)
        elif self.state == BBRState.PROBE_BW:
            self.pacing_rate = min(1.25 * self.max_bw, self.max_pacing_rate)
        elif self.state == BBRState.PROBE_RTT:
            self.pacing_rate = min(self.max_bw, self.max_pacing_rate)

    def _update_bandwidth_rtt(self, lost=False):
        if not lost:
            delivered_rate = self.bytes_sent / self.time
            self.max_bw = max(self.max_bw, delivered_rate)
            self.min_rtt = min(self.min_rtt, self.rtt)
        self.cwnd = self._get_cwnd()

    def _get_cwnd(self):
        if self.state == BBRState.STARTUP:
            return min(2 * self.cwnd, self._bdp() * 2)
        elif self.state == BBRState.PROBE_RTT:
            return 4
        else:
            return self._bdp()

    def _bdp(self):
        return self.max_bw * self.min_rtt

    def _bw_decreased(self):
        return self.max_bw > 0 and self.bytes_sent / self.time < 0.75 * self.max_bw

    def _inflight(self):
        return self.bytes_sent - self.ack

    def _record_metrics(self):
        self.times.append(self.time)
        self.cwnds.append(self.cwnd)
        self.bw_estimates.append(self.max_bw)
        self.rtt_estimates.append(self.min_rtt)
        self.states.append(self.state)
        self.throughput.append(self.bytes_sent / self.time)

    def plot_metrics(self):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot congestion window
        ax1.plot(self.times, self.cwnds)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Congestion Window (packets)')
        ax1.set_title('BBR Congestion Window')
        
        # Plot bandwidth estimates
        ax2.plot(self.times, self.bw_estimates)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Bandwidth Estimate (bytes/s)')
        ax2.set_title('BBR Bandwidth Estimates')
        
        # Plot RTT estimates
        ax3.plot(self.times, self.rtt_estimates)
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('RTT Estimate (s)')
        ax3.set_title('BBR RTT Estimates')
        
        # Plot throughput
        ax4.plot(self.times, self.throughput)
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Throughput (bytes/s)')
        ax4.set_title('Network Throughput')
        
        plt.tight_layout()
        plt.show()

def simulate_bbr():
    client = TCPBBRConnection('Client', rtt=0.15, loss_rate=0.02, max_packets=10000)
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
    simulate_bbr()