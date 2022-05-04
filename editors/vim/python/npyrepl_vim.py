from queue import Queue
import re
import socket
from textwrap import indent
from threading import Thread
from types import SimpleNamespace as SN

import vim

try:
    from npyrepl.encoding import write_packet, read_packet
    from npyrepl.server import PORT_FILE_PATH
except:
    pass

session = SN(
    queue=Queue(),
    running=False,
)

def session_loop():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = read_port_file()
        sock.connect(("localhost", port))
        _print(f"Connected to localhost:{port}")

        session.wsock = sock.makefile("wb")
        session.rsock = sock.makefile("rb")

        session.running = True
        while session.running:
            command = session.queue.get()
            try:
                command()
            except Exception as ex:
                _print(ex)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

def read_port_file():
    with PORT_FILE_PATH.open("r") as port_file:
        return int(port_file.read())

def connect():
    if session.running:
        _print("Already connected")
        return

    thread = Thread(target=session_loop)
    thread.daemon = True
    thread.start()

def disconnect():
    if session.running:
        def command():
            session.running = False
        session.queue.put(command)
    else:
        _print("Not connected")

def eval_code(code):
    assert session.running
    def command():
        _send_packet(SN(op="eval", code=code),
            lambda response: _print(f"Result: {response.value}"))
    session.queue.put(command)

def eval_lines():
    rng = vim.current.range
    lines = "\n".join(vim.current.buffer[rng.start:rng.end+1])
    eval_code(lines)

def eval_buffer():
    eval_code("\n".join(vim.current.buffer))

def eval_global_function():
    row = vim.current.window.cursor[0] - 1
    function_code = _extract_global_function(vim.current.buffer, row)
    if function_code is not None:
        eval_code(function_code)
    else:
        _print("Failed to extract function code")

def namespace(name):
    assert session.running
    def command():
        _send_packet(SN(op="ns", name=name or ""),
            lambda response: _print(f"Current namespace: {response.ns}"))
    session.queue.put(command)

def _extract_global_function(buffer, row):
    is_global_statement = lambda line: not re.match(r"$|\s|#", line)

    def find_beginning():
        for line_idx in range(row, -1, -1):
            line = buffer[line_idx]
            if is_global_statement(line):
                if re.match("def ", line):
                    return line_idx
                else:
                    return None
        return None

    def find_ending():
        for line_idx in range(row + 1, len(buffer)):
            line = buffer[line_idx]
            if is_global_statement(line):
                return line_idx
        return len(buffer)

    beginning = find_beginning()
    ending = find_ending()
    if beginning is not None:
        return "\n".join(buffer[beginning:ending]).strip()
    return None

def _send_packet(packet, handle_response):
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
