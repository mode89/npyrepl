import ast
from functools import reduce
from pathlib import Path
from socketserver import StreamRequestHandler, ThreadingTCPServer, TCPServer
from types import ModuleType
from types import SimpleNamespace as SN

from .encoding import read_packet, write_packet

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
                    expr = request.expr.strip()
                    try:
                        if expr == "":
                            pass
                        elif expr == "__main__":
                            namespace = main_namespace
                        else:
                            new_namespace = eval(expr, vars(namespace))
                            if not isinstance(new_namespace, ModuleType):
                                raise TypeError("Must be a module")
                            namespace = new_namespace
                        write_packet(self.wfile, SN(ns=namespace.__name__))
                    except Exception as ex:
                        write_packet(self.wfile, SN(ex=str(ex)))
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
