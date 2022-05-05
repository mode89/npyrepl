import re
import socket
import readline
from textwrap import indent
from types import SimpleNamespace as SN

from .encoding import read_packet, write_packet

def read_command(prompt_prefix=""):
    lines = []
    while True:
        prompt = prompt_prefix + ("> " if not lines else ". ")
        line = input(prompt).rstrip()
        if not line:
            if lines:
                break
            else:
                continue
        lines.append(line)
        if line[-1] != ":" and len(lines) == 1:
            break
    return "\n".join(lines)

def run(address, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((address, port))
        print(f"Console connected to {address}:{port}")

        wfile = sock.makefile("wb")
        rfile = sock.makefile("rb")

        state = SN()

        def handle_command(packet, handle_response):
            write_packet(wfile, packet)
            wfile.flush()
            response = read_packet(rfile)
            ex = getattr(response, "ex", None)
            if ex is None:
                handle_response(response)
            else:
                print(f"Server exception:\n{indent(ex.strip(), '  ')}")

        def update_namespace(response):
            state.ns = response.ns

        handle_command(SN(op="ns", name=""), update_namespace)

        while True:
            try:
                command = read_command(f"{state.ns} ")
            except EOFError:
                break

            # Special commands
            if command[0] == ":":
                # Change namespace
                if command.startswith(":ns"):
                    name = command[3:].strip()
                    handle_command(
                        SN(op="ns", name=name),
                        update_namespace)
                # Exit the console
                elif command == ":exit":
                    break
                else:
                    print(f"Unknown command {command}")
            # Evaluate entered code
            else:
                handle_command(
                    SN(op="eval", code=command),
                    lambda response: print(response.value))
