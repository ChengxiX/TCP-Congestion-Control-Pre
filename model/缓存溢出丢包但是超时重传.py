import asyncio
from frame import TCPConnection, Router, TCPPacket, TCPConnectionWithTimeout

"""尽管有超时重传，但是返回的ack丢了就很尴尬。不具有滑动发包"""


async def main():
    # 初始化路由器
    router = Router(send_interval=0.1, max_buffer_size=10)

    # 初始化服务器
    server = TCPConnectionWithTimeout(name='Server', router=router)
    
    # 初始化客户端
    client = TCPConnectionWithTimeout(name='Client', router=router, timeout=1.5)
    
    # 建立连接（三次握手）
    syn = TCPPacket(seq=1, syn=True)
    await client.send(syn, server)
    
    # 等待连接建立
    await asyncio.sleep(0.1)
    
    # 客户端均匀发送数据
    for i in range(50):
        data = f'Hello, Server! Message {i+1}'
        data_packet = TCPPacket(seq=2 + i, ack=1, data=data)
        await client.send(data_packet, server)
        await asyncio.sleep(0.01)  # 均匀间隔发送
    
    # 等待数据传输
    await asyncio.sleep(100)
    
    # 客户端发送FIN包断开连接
    fin = TCPPacket(seq=7, ack=1, fin=True)
    await client.send(fin, server)
    
    # 等待断开
    await asyncio.sleep(1)

# 运行演示
if __name__ == "__main__":
    asyncio.run(main())