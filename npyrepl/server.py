import ast
from functools import reduce
from importlib import import_module
from pathlib import Path
from socketserver import StreamRequestHandler, ThreadingTCPServer, TCPServer
from traceback import format_exc
from types import ModuleType
from types import SimpleNamespace as SN

from .encoding import read_packet, write_packet

PORT_FILE_PATH = Path(".npyrepl-port")

_op_handlers = {}

def run(address, port):
    server = SN(
        main_namespace=SN(__name__="__main__"),
        client_counter=0,
    )

    class RequestHandler(StreamRequestHandler):
        def handle(self):
            client_handler(server, self.rfile, self.wfile)

    with ThreadingTCPServer((address, port), RequestHandler) as tcp_server:
        port = tcp_server.socket.getsockname()[1]
        print(f"Server is running on {address}:{port}")
        with PORT_FILE_PATH.open("w") as port_file:
            port_file.write(str(port))
        try:
            tcp_server.serve_forever()
        finally:
            PORT_FILE_PATH.unlink()

def client_handler(server, rsock, wsock):
    server.client_counter += 1
    print("New client connected. Number of connected clients: "
        f"{server.client_counter}")

    client = SN(
        namespace=server.main_namespace,
    )

    while True:
        request = read_packet(rsock)
        if request is None:
            break

        try:
            op_handler_ = _op_handlers[request.op]
            response = op_handler_(server, client, request)
        except:
            response = SN(ex=format_exc())
        write_packet(wsock, response)

    server.client_counter -= 1
    print("Client disconnected. Number of connected clients: "
        f"{server.client_counter}")

def op_handler(op):
    def wrapper(f):
        _op_handlers[op] = f
        return f
    return wrapper

@op_handler("eval")
def _evaluate(server, client, request):
    namespace = vars(client.namespace)
    code = request.code
    parsed = ast.parse(code)
    statements = parsed.body
    if len(statements) == 1 and isinstance(statements[0], ast.Expr):
        result = eval(code, namespace)
    else:
        exec(code, namespace)
        result = None
    return SN(value=str(result))

@op_handler("ns")
def _namespace(server, client, request):
    if request.name == "":
        pass
    elif request.name == "__main__":
        client.namespace = server.main_namespace
    else:
        client.namespace = import_module(request.name)
    return SN(ns=client.namespace.__name__)
