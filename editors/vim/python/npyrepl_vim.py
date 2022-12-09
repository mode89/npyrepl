import ast
import re
import socket
from textwrap import indent
from types import SimpleNamespace as SN

import vim

try:
    from npyrepl.encoding import write_packet, read_packet
    from npyrepl.server import PORT_FILE_PATH
    NPYREPL_FOUND = True
except:
    NPYREPL_FOUND = False

session = SN(
    sock=None,
)

def read_port_file():
    with PORT_FILE_PATH.open("r") as port_file:
        return int(port_file.read())

def connect(*args):
    if not NPYREPL_FOUND:
        raise RuntimeError("npyrepl python module wasn't found")

    if len(args) == 0:
        address = "localhost"
        port = read_port_file()
    elif len(args) == 1:
        address = "localhost"
        port = int(args[0])
    elif len(args) == 2:
        address = args[0]
        port = int(args[1])
    else:
        _print("NpyreplConnect expects no more than two arguments")
        return

    if session.sock:
        _print("Closing existing connection ...")
        session.sock.shutdown(socket.SHUT_RDWR)
        session.sock.close()
        session.sock = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", port))
    _print(f"Connected to localhost:{port}")

    session.sock = sock
    session.wsock = sock.makefile("wb")
    session.rsock = sock.makefile("rb")

def disconnect():
    if session.sock:
        session.sock.shutdown(socket.SHUT_RDWR)
        session.sock.close()
        session.sock = None
    else:
        _print("Not connected")

def eval_code(code):
    _send_packet(SN(op="eval", code=code),
        lambda response: _print(f"Result: {response.value}"))

def eval_lines():
    rng = vim.current.range
    lines = "\n".join(vim.current.buffer[rng.start:rng.end+1])
    eval_code(lines)

def eval_buffer():
    eval_code("\n".join(vim.current.buffer))

def eval_global_statement():
    row = vim.current.window.cursor[0]
    statement_code = _extract_global_statement(vim.current.buffer, row)
    if statement_code is not None:
        eval_code(statement_code)
    else:
        _print("No global statement selected")

def namespace(name):
    _send_packet(SN(op="ns", name=name or ""),
        lambda response: _print(f"Current namespace: {response.ns}"))

def _extract_global_statement(buffer, row):
    buffer_str = "\n".join(buffer[:])
    module = ast.parse(buffer_str)
    for node in ast.iter_child_nodes(module):
        first_line = node.lineno
        last_line = node.end_lineno
        if row >= first_line and row <= last_line:
            return "\n".join(buffer[first_line-1:last_line])
    return None

def _send_packet(packet, handle_response):
    assert session.sock, "Not connected to server"
    write_packet(session.wsock, packet)
    session.wsock.flush()
    response = read_packet(session.rsock)
    ex = getattr(response, "ex", None)
    if ex is None:
        handle_response(response)
    else:
        _print(f"Server exception:\n{indent(ex.strip(), '  ')}")

def _print(msg):
    for line in msg.split("\n"):
        line_ = line.replace("\"", "\\\"")
        vim.command(f"echomsg \"{line_}\"")
