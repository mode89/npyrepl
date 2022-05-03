import re
import socket

from .encoding import read_packet, write_packet

def read_port_file():
    with open(".npyrepl-port", "r") as port_file:
        return int(port_file.read())

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

def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", read_port_file()))
        wfile = sock.makefile("wb")
        rfile = sock.makefile("rb")

        state = {
            "ns": ""
        }

        def handle_command(packet, handle_response):
            write_packet(wfile, packet)
            wfile.flush()
            response = read_packet(rfile)
            ex = response.get("ex", None)
            if ex is None:
                handle_response(response)
            else:
                print(ex)

        while True:
            try:
                ns = state["ns"]
                command = read_command("" if not ns else f"{ns} ")
            except EOFError:
                break

            # Special commands
            if command[0] == ":":
                # Change namespace
                if command.startswith(":ns"):
                    def update_namespace(response):
                        state["ns"] = response["ns"]
                    handle_command(
                        { "op": "ns", "expr": command[3:] },
                        update_namespace)
                # Exit the console
                elif command == ":exit":
                    break
                else:
                    print(f"Unknown command {command}")
            # Evaluate entered code
            else:
                handle_command(
                    { "op": "eval", "code": command },
                    lambda response: print(response["value"]))
