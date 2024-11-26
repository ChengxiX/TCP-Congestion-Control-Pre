
import asyncio
from frame import SlidingWindowTCPConnection, Router, TCPPacket

async def main():
    router = Router(send_interval=0.003, max_buffer_size=100)

    sender = SlidingWindowTCPConnection(
        name="Sender",
        router=router,
        rtt=0.1,
        max_packets=100,
        jitter=0.02,
        loss_rate=0.05,
        timeout=0.5,
        window_size=5
    )

    receiver = SlidingWindowTCPConnection(
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
    for i in range(1, 21):
        data = f"Message {i}"
        packet = TCPPacket(seq=i, ack=0, syn=False, ack_flag=False, fin=False, data=data)
        await sender.send(packet, receiver)
        await asyncio.sleep(0.05)  # 模拟应用层发送间隔

    # 等待所有包传输完成
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())