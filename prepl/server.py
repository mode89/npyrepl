from functools import reduce
from pathlib import Path
from socketserver import StreamRequestHandler, ThreadingTCPServer, TCPServer

from .encoding import read_packet, write_packet

def run():

    class RequestHandler(StreamRequestHandler):

        def handle(self):
            while True:
                request = read_packet(self.rfile)
                if request is None:
                    break

                if request["op"] == "eval":
                    value, ex = evaluate(request["code"])
                    if ex is None:
                        write_packet(self.wfile, {
                            "value": str(value),
                        })
                    else:
                        write_packet(self.wfile, {
                            "ex": str(ex),
                        })
                else:
                    raise RuntimeError(f"Unknown request: {request}")

    with ThreadingTCPServer(("localhost", 0), RequestHandler) as server:

        port = server.socket.getsockname()[1]
        print(f"Server is running on port: {port}")
        prepl_port_path = Path(".prepl-port")
        with prepl_port_path.open("w") as port_file:
            port_file.write(str(port))
        try:
            server.serve_forever()
        finally:
            prepl_port_path.unlink()

def evaluate(code):
    try:
        return eval(code), None
    except Exception as ex:
        return None, ex

if __name__ == "__main__":
    run()
