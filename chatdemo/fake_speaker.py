from easyconnects import Client

client = Client('speaker', sr=44100, latency=0.5, blocksize=2048)
while True:
    client.send(b'')
    wav, sr, expire_time = client.recv_pyobj()
    print(f'audio +{expire_time:5.2f}')