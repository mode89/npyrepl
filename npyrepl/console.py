from pathlib import Path
import re
import readline
import socket
from textwrap import indent
from types import SimpleNamespace as SN

from .encoding import read_packet, write_packet

HIST_FILE = Path.home() / ".npyrepl_history"

def run(address, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((address, port))
        print(f"Console connected to {address}:{port}")

        state = SN(
            wsock=sock.makefile("wb"),
            rsock=sock.makefile("rb"),
            running=True,
        )

        _namespace(state, ":ns")

        try:
            if not HIST_FILE.exists():
                HIST_FILE.touch()
            readline.read_history_file(HIST_FILE)
            while state.running:
                try:
                    command = _read_command(f"{state.ns} ")
                except EOFError:
                    break

                # Special commands
                if command[0] == ":":
                    cmd_names = list(filter(
                        lambda cmd: command.startswith(cmd),
                        _command.handlers.keys()))
                    if not cmd_names:
                        print(f"Unknown command {command}")
                    elif len(cmd_names) > 1:
                        print(f"Ambiguous command {command}")
                    else:
                        handler = _command.handlers[cmd_names[0]]
                        handler(state, command)
                # Evaluate entered code
                else:
                    _evaluate_code(state, command)
        finally:
            readline.write_history_file(HIST_FILE)

def _send_packet(state, packet, handle_response):
    write_packet(state.wsock, packet)
    state.wsock.flush()
    response = read_packet(state.rsock)
    ex = getattr(response, "ex", None)
    if ex is None:
        handle_response(response)
    else:
        print(f"Server exception:\n{indent(ex.strip(), '  ')}")

def _read_command(prompt_prefix=""):
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

def _command(name):
    def wrapper(f):
        if not hasattr(_command, "handlers"):
            _command.handlers = {}
        _command.handlers[name] = f
        return f
    return wrapper

@_command(":ns")
def _namespace(state, command):
    name = command[3:].strip()
    def update_namespace(response):
        state.ns = response.ns
    _send_packet(state,
        SN(op="ns", name=name),
        update_namespace)

@_command(":exit")
def _exit(state, _):
    state.running = False

def _evaluate_code(state, command):
    _send_packet(state,
        SN(op="eval", code=command),
        lambda response: print(response.value))
