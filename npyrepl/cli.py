from argparse import ArgumentParser
from . import server
from . import console

def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    server_parser = subparsers.add_parser("server",
        description="Run REPL server only.")
    server_parser.add_argument("--port", "-p",
        help="Port of the REPL server",
        type=int,
        default=None)
    server_parser.add_argument("--address", "-a",
        help="Network address of the REPL server",
        default=None)
    console_parser = subparsers.add_parser("console",
        description="Run REPL console client.")
    console_parser.add_argument("--port", "-p",
        help="Port of the REPL server",
        type=int,
        default=None)
    console_parser.add_argument("--address", "-a",
        help="Network address of the REPL server",
        default=None)
    args = parser.parse_args()

    if args.command == "server":
        port = args.port or 0
        address = args.address or "0.0.0.0"
        server.run(address, port)
    elif args.command == "console":
        port = args.port or read_port_file()
        address = args.address or "localhost"
        console.run(address, port)
    else:
        parser.print_help()

def read_port_file():
    with server.PORT_FILE_PATH.open("r") as port_file:
        return int(port_file.read())
