from argparse import ArgumentParser
from concurrent.futures import Future
from threading import Thread
from . import server
from . import console

def main():
    parser = ArgumentParser()
    parser.add_argument("--port", "-p",
        help="Port of the REPL server",
        type=int,
        default=None)
    parser.add_argument("--address", "-a",
        help="Network address of the REPL server",
        default=None)
    parser.add_argument("--server",
        help="Run only the REPL server",
        action="store_true")
    parser.add_argument("--console",
        help="Run only the console client and connect to an existing "
            "REPL server",
        action="store_true")
    args = parser.parse_args()

    if args.server:
        port = args.port or 0
        address = args.address or "0.0.0.0"
        with server.start(address, port) as srv:
            srv.serve()
    elif args.console:
        port = args.port or read_port_file()
        address = args.address or "localhost"
        console.run(address, port)
    else:
        port = args.port or 0
        address = args.address or "0.0.0.0"
        srv_future = Future()
        def server_thread():
            with server.start(address, port) as srv:
                srv_future.set_result(srv)
                srv.serve()
        Thread(target=server_thread).start()
        srv = srv_future.result()
        try:
            console.run("localhost", srv.port)
        finally:
            srv.shutdown()

def read_port_file():
    with server.PORT_FILE_PATH.open("r") as file:
        return int(file.read())
