from argparse import ArgumentParser
from . import server
from . import console

def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    server_parser = subparsers.add_parser("server",
        description="Run REPL server only.")
    console_parser = subparsers.add_parser("console",
        description="Run REPL console client.")
    args = parser.parse_args()

    if args.command == "server":
        server.run()
    elif args.command == "console":
        console.run()
    else:
        parser.print_help()
