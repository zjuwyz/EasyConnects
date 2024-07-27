import asyncio
from easyconnects.asyncio import Server, Socket
import zmq
import zmq.asyncio

# A sample server that transfers data between alice and bob.
# Queueing message if one side is offline.
class SampleServer(Server):
q
    # Using two queues for tunneling data between clients: Alice and Bob
    alice_queue = asyncio.Queue()
    bob_queue = asyncio.Queue()

    @staticmethod
    async def _handle_client(socket: Socket, meta, queue_in: asyncio.Queue, queue_out: asyncio.Queue):
        print(f"Client connected with meta: {meta}")

        async def send_message():
            while True:
                msg = await queue_out.get()
                await socket.send(msg)
     
        async def recv_message():
            while True:
                msg = await socket.recv()
                await queue_in.put(msg)
              
        send_task = asyncio.create_task(send_message())
        recv_task = asyncio.create_task(recv_message())
        await asyncio.gather(send_task, recv_task)

    @staticmethod
    async def handle_alice(socket: Socket, meta):
        await SampleServer._handle_client(socket, meta, SampleServer.alice_queue, SampleServer.bob_queue)

    @staticmethod
    async def handle_bob(socket: Socket, meta):
        await SampleServer._handle_client(socket, meta, SampleServer.bob_queue, SampleServer.alice_queue)

async def main():
   await SampleServer().serve()

if __name__ == "__main__":
   asyncio.run(main())
