import matplotlib.pyplot as plt
import numpy as np

def simulate_bbr():
    time_total = 60
    times = np.linspace(0, time_total, 500)
    cwnd = []
    throughput = []
    loss_events = []

    bandwidth = 1000
    rtt = 0.1
    gain = 1.25
    drain = 0.75

    cwnd_smoothing_factor = 0.05
    throughput_smoothing_factor = 0.05

    cycle_duration = 1
    cycle_start_time = 0
    current_phase = 0  # 0: Startup, 1: Probe BW, 2: Drain, 3: Probe RTT

    for t in times:
        if t - cycle_start_time >= cycle_duration:
            cycle_start_time = t
            current_phase = (current_phase + 1) % 4
            if current_phase == 0:
                if np.random.rand() < 0.1:
                    gain += np.random.uniform(-0.05, 0.05)
                    drain += np.random.uniform(-0.05, 0.05)
                    gain = max(1.0, min(gain, 1.5))
                    drain = max(0.5, min(drain, 0.9))


        if current_phase == 0: # Startup
            target_cwnd = min(2 * len(cwnd) + 1 if len(cwnd) > 0 else 2, 100)
        elif current_phase == 1:  # Probe bandwidth
            target_cwnd = int(bandwidth * rtt * gain)
        elif current_phase == 2: # Drain
            target_cwnd = int(bandwidth * rtt * drain)
        elif current_phase == 3: # Probe RTT
            target_cwnd = int(bandwidth * rtt)

        if len(cwnd) > 0:
            smoothed_cwnd = cwnd[-1] * (1 - cwnd_smoothing_factor) + target_cwnd * cwnd_smoothing_factor
            cwnd.append(int(smoothed_cwnd))
        else:
            cwnd.append(int(target_cwnd))

        current_throughput = cwnd[-1] / rtt * 1500
        if len(throughput) > 0:
            smoothed_throughput = throughput[-1] * (1 - throughput_smoothing_factor) + current_throughput * throughput_smoothing_factor
            throughput.append(int(smoothed_throughput))
        else:
            throughput.append(int(current_throughput))

        if np.random.rand() < 0.01:
            loss_events.append(t)
            bandwidth *= 0.8

    return times, cwnd, throughput, loss_events


def plot_metrics(times, cwnds, throughput, loss_events):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(times, cwnds)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Congestion Window (packets)')
    ax1.set_title('TCP BBR Congestion Window')

    ax2.plot(times, throughput)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Throughput (bytes/s)')
    ax2.set_title('Network Throughput')

    for loss_time in loss_events:
        ax1.axvline(x=loss_time, color='red', alpha=0.3, linestyle='--')
        ax2.axvline(x=loss_time, color='red', alpha=0.3, linestyle='--')

    ax1.plot([], [], color='red', linestyle='--', label='Packet Loss')
    ax1.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    times, cwnds, throughput, loss_events = simulate_bbr()
    plot_metrics(times, cwnds, throughput, loss_events)