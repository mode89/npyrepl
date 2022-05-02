import socket

from .encoding import read_packet, write_packet

def read_port_file():
    with open(".prepl-port", "r") as port_file:
        return int(port_file.read())

def read_command():
    lines = []
    while True:
        prompt = "> " if not lines else ". "
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

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", read_port_file()))
        wfile = sock.makefile("wb")
        rfile = sock.makefile("rb")

        while True:
            try:
                command = read_command()
            except EOFError:
                break
            if command[0] == ":":
                if command == ":exit":
                    break
                else:
                    print(f"Unknown command {command}")
            else:
                write_packet(wfile, {
                    "op": "eval",
                    "code": command,
                })
                wfile.flush()
                result = read_packet(rfile)
                ex = result.get("ex", None)
                if ex is None:
                    print(result["value"])
                else:
                    print(ex)
