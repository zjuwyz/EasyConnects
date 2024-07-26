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

## Notice:
* `Server` is using `asyncio` for easier concurrency, while `Client` is using normal, blocking api to easier integrate with existing code.
* Only one `Server` can exists at the same time, since binding url is fixed to `tcp://*:12000`. 
this can be changed in `easyconnects.__init__.py`. 
If you pip installed with `-e` flag, it will take effect immediately, otherwise you'll have to reinstall. 
There may be furthur updates on this.
