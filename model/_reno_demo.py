import asyncio
from Reno import RenoTCPConnection, TCPPacket
from frame import Router
import matplotlib.pyplot as plt

async def main():
    router = Router(send_interval=0.01, max_buffer_size=50)

    sender = RenoTCPConnection(
        name="Sender",
        router=router,
        rtt=0.1,
        max_packets=100,
        jitter=0.02,
        loss_rate=0.05,
        timeout=0.5,
        window_size=5
    )

    receiver = RenoTCPConnection(
        name="Receiver",
        router=router,
        rtt=0.1,
        max_packets=100,
        jitter=0.02,
        loss_rate=0.05,
        timeout=0.5,
        window_size=5
    )

    # 发送数据
    for i in range(1, 50):
        data = f"Message {i}"
        packet = TCPPacket(seq=i, ack=0, syn=False, ack_flag=False, fin=False, data=data)
        await sender.send(packet, receiver)
       await asyncio.sleep(0.02)  # 模拟应用层发送间隔

    # 等待所有包传输完成
    await asyncio.sleep(20)

    # 绘制cwnd变化图
    plt.figure(figsize=(10, 6))
    plt.plot(sender.cwnd_history, marker='o')
    plt.title('Reno 拥塞窗口 (cwnd) 变化图')
    plt.xlabel('事件序号')
    plt.ylabel('拥塞窗口大小 (cwnd)')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())