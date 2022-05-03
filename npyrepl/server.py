import ast
from functools import reduce
from pathlib import Path
from socketserver import StreamRequestHandler, ThreadingTCPServer, TCPServer
from types import ModuleType

from .encoding import read_packet, write_packet

def run():
    default_namespace = dict()

    class RequestHandler(StreamRequestHandler):

        def handle(self):
            namespace = default_namespace
            while True:
                request = read_packet(self.rfile)
                if request is None:
                    break

                if request["op"] == "eval":
                    value, ex = evaluate(request["code"], namespace)
                    if ex is None:
                        write_packet(self.wfile, {
                            "value": str(value),
                        })
                    else:
                        write_packet(self.wfile, {
                            "ex": str(ex),
                        })
                elif request["op"] == "ns":
                    expr = request["expr"]
                    if expr == "":
                        namespace = default_namespace
                        write_packet(self.wfile, {
                            "ns": "",
                        })
                    else:
                        try:
                            namespace_module = eval(expr, namespace)
                            if not isinstance(namespace_module, ModuleType):
                                raise TypeError("Must be a module")
                            namespace = vars(namespace_module)
                            write_packet(self.wfile, {
                                "ns": str(namespace_module.__name__),
                            })
                        except Exception as ex:
                            write_packet(self.wfile, {
                                "ex": str(ex),
                            })
                else:
                    raise RuntimeError(f"Unknown request: {request}")

    with ThreadingTCPServer(("localhost", 0), RequestHandler) as server:
        port = server.socket.getsockname()[1]
        print(f"Server is running on port: {port}")
        npyrepl_port_path = Path(".npyrepl-port")
        with npyrepl_port_path.open("w") as port_file:
            port_file.write(str(port))
        try:
            server.serve_forever()
        finally:
            npyrepl_port_path.unlink()

def evaluate(code, namespace):
    try:
        parsed = ast.parse(code)
        for statement in parsed.body:
            if isinstance(statement, ast.Expr):
                return eval(code, namespace), None
            else:
                exec(code, namespace)
                return None, None
    except Exception as ex:
        return None, ex
