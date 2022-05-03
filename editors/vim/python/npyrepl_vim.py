from queue import Queue
import socket
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

def eval(expr):
    assert session.running
    def command():
        _send_packet(SN(op="eval", code=expr),
            lambda response: _print(f"Result: {response.value}"))
    session.queue.put(command)

def eval_lines():
    assert session.running
    rng = vim.current.range
    lines = "\n".join(vim.current.buffer[rng.start:rng.end+1])
    def command():
        _send_packet(SN(op="eval", code=lines),
            lambda response: _print(f"Result: {response.value}"))
    session.queue.put(command)

def namespace(expr):
    assert session.running
    def command():
        _send_packet(SN(op="ns", expr=expr or ""),
            lambda response: _print(f"Current namespace: {response.ns}"))
    session.queue.put(command)

def _send_packet(packet, handle_response):
    write_packet(session.wsock, packet)
    session.wsock.flush()
    response = read_packet(session.rsock)
    ex = getattr(response, "ex", None)
    if ex is None:
        handle_response(response)
    else:
        _print(ex)

def _print(msg):
    vim.command(f"echomsg \"{msg}\"")
