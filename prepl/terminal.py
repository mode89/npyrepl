import socket

from .encoding import read_packet, write_packet

def read_port_file():
    with open(".prepl-port", "r") as port_file:
        return int(port_file.read())

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", read_port_file()))
        wfile = sock.makefile("wb")
        rfile = sock.makefile("rb")

        while True:
            command = input("> ").strip()
            if command:
                write_packet(wfile, {
                    "op": "eval",
                    "code": command,
                })
                wfile.flush()
                result = read_packet(rfile)
                ex = result.get("ex", None)
                if ex is None:
                    print(result["value"])
                else:
                    print(ex)
