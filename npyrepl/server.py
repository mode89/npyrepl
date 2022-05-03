import ast
from functools import reduce
from importlib import import_module
from pathlib import Path
from socketserver import StreamRequestHandler, ThreadingTCPServer, TCPServer
from types import ModuleType
from types import SimpleNamespace as SN

from .encoding import read_packet, write_packet

PORT_FILE_PATH = Path(".npyrepl-port")

def run():
    main_namespace = SN(__name__="__main__")
    server_state = SN(client_counter=0)

    class RequestHandler(StreamRequestHandler):

        def handle(self):
            server_state.client_counter += 1
            print("New client connected. Number of connected clients: "
                f"{server_state.client_counter}")

            namespace = main_namespace
            while True:
                request = read_packet(self.rfile)
                if request is None:
                    break

                try:
                    if request.op == "eval":
                        value = _evaluate(request.code, vars(namespace))
                        write_packet(self.wfile, SN(value=str(value)))
                    elif request.op == "ns":
                        if request.name == "":
                            pass
                        elif request.name == "__main__":
                            namespace = main_namespace
                        else:
                            namespace = import_module(request.name)
                        write_packet(self.wfile, SN(ns=namespace.__name__))
                    else:
                        raise RuntimeError(f"Unknown request: {request}")
                except Exception as ex:
                    write_packet(self.wfile, SN(ex=str(ex)))

            server_state.client_counter -= 1
            print("Client disconnected. Number of connected clients: "
                f"{server_state.client_counter}")

    with ThreadingTCPServer(("localhost", 0), RequestHandler) as server:
        port = server.socket.getsockname()[1]
        print(f"Server is running on port: {port}")
        with PORT_FILE_PATH.open("w") as port_file:
            port_file.write(str(port))
        try:
            server.serve_forever()
        finally:
            PORT_FILE_PATH.unlink()

def _evaluate(code, namespace):
    parsed = ast.parse(code)
    statements = parsed.body
    if len(statements) == 1 and isinstance(statements[0], ast.Expr):
        return eval(code, namespace)
    else:
        exec(code, namespace)
        return None
