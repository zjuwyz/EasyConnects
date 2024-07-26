# EasyConnects - A Socket Utility Module
EasyConnects is a simple and lightweight Python module that provides a socket server utility, facilitating communication between different components of your application. It uses the ZeroMQ library for efficient and reliable messaging.
EasyConnects is a simple and lightweight Python module that provides a socket server utility, making communication between different components of your application easy. It uses the ZeroMQ library for efficient and reliable messaging.

## Installation


```bash
git clone https://github.com/wangyize/easyconnects.git
cd easyconnects.git
pip install .
```
## Usage
Here's a basic example of how to use EasyConnects in your project:

### Server
```Python
from easyconnects import Server
import asyncio

class MyServer(Server):
    async def handle_my_service(self, socket, meta):
        # The meta argument contains additional information about the client.
        print("Meta data:", meta)
        while True:
            message = await socket.recv_json()
            # Process the message here

async def main():
    server = MyServer()
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())

```
In this example, handle_my_service is a coroutine that handles the communication for a service named "my_service". The meta argument contains additional information about the connection, which can be passed from the client when connecting.

### Client
```Python
from easyconnects import Client
import asyncio

async def main():
    # You can pass additional information using keyword arguments (kwargs)
    client = Client("my_service", user="Alice", role="admin")
    await client.send_json({"message": "Hello, Server!"})

if __name__ == "__main__":
    asyncio.run(main())
```
In this example, the client is connecting to a service named "my_service". It sends a JSON message to the server using send_json. The additional information (user and role) is sent as keyword arguments when creating the Client instance and can be accessed on the server side.
Currently, the `Server` class utilizes `asyncio`, while the `Client` class is synchronous/blocking. In the future, we may implement asynchronous `Client` functionality and a thread-based `Server`.

The `Server` employs `asyncio` for efficient handling of concurrent connections. The `Client`, on the other hand, operates synchronously/blocking in its current implementation. In future updates, we aim to implement asynchronous client functionality and a thread-based server design to improve performance and efficiency.
