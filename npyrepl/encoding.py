import json
import struct

def read_packet_size(f):
    data = str()
    while True:
        char = f.read(1)
        if len(char) == 0:
            return None
        elif char == b":":
            return int(data)
        else:
            data = data + char.decode("utf-8")[0]

def read_packet(f):
    size = read_packet_size(f)
    if size is not None:
        data_json = f.read(size).decode("utf-8")
        data = json.loads(data_json)
        return data
    else:
        return None

def write_packet(f, data):
    data_json = json.dumps(data)
    size = len(data_json)
    f.write(f"{size}:{data_json}".encode("utf-8"))
