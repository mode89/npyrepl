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

    class RequestHandler(StreamRequestHandler):

        def handle(self):
            namespace = main_namespace
            while True:
                request = read_packet(self.rfile)
                if request is None:
                    break

                if request.op == "eval":
                    value, ex = evaluate(request.code, vars(namespace))
                    if ex is None:
                        write_packet(self.wfile, SN(value=str(value)))
                    else:
                        write_packet(self.wfile, SN(ex=str(ex)))
                elif request.op == "ns":
                    try:
                        if request.name == "":
                            pass
                        elif request.name == "__main__":
                            namespace = main_namespace
                        else:
                            namespace = import_module(request.name)
                        write_packet(self.wfile, SN(ns=namespace.__name__))
                    except Exception as ex:
                        write_packet(self.wfile, SN(ex=str(ex)))
                else:
                    raise RuntimeError(f"Unknown request: {request}")

    with ThreadingTCPServer(("localhost", 0), RequestHandler) as server:
        port = server.socket.getsockname()[1]
        print(f"Server is running on port: {port}")
        with PORT_FILE_PATH.open("w") as port_file:
            port_file.write(str(port))
        try:
            server.serve_forever()
        finally:
            PORT_FILE_PATH.unlink()

def evaluate(code, namespace):
    try:
        parsed = ast.parse(code)
        statements = parsed.body
        if len(statements) == 1 and isinstance(statements[0], ast.Expr):
            return eval(code, namespace), None
        else:
            exec(code, namespace)
            return None, None
    except Exception as ex:
        return None, ex
