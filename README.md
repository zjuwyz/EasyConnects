# EasyConnects - A Socket Utility Module
EasyConnects is a simple and lightweight Python module that provides a socket server utility, making communication between different components of your application easy. It uses the ZeroMQ library for efficient and reliable messaging.

## Installation


```bash
git clone https://github.com/zjuwyz/easyconnects.git
cd easyconnects
pip install .
```
## Usage
see `server.py` and `client.py`
### Notice:
* `Server` is using asyncio for handling multipe clients., But `Client` is using blocking api, to make it easier to integrate with existing code.
* Only one `Server` can exists on one host at the same time. They use hardcoded port 12000. Change this in `easyconnects.__init__.py`. There may be furthur updates on this.
