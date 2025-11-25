"""Small stdio<->TCP proxy wrapper used by the backend for reliable stdio proxying.

This script is intentionally tiny: it connects to the backend proxy port and
forwards stdin->socket and socket->stdout. The backend will spawn the real
MCP child and bridge the socket to the child's stdio.

Environment variables:
- MCP_PROXY_HOST (default: 127.0.0.1)
- MCP_PROXY_PORT (required)
"""
import os
import sys
import socket


def main():
    host = os.environ.get("MCP_PROXY_HOST", "127.0.0.1")
    port = os.environ.get("MCP_PROXY_PORT")
    logpath = None
    try:
        logdir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logdir, exist_ok=True)
        logpath = os.path.join(logdir, 'mcp_stdio_wrapper.log')
    except Exception:
        logpath = None

    if not port:
        msg = "MCP_PROXY_PORT not set"
        try:
            if logpath:
                with open(logpath, 'a', encoding='utf-8') as lf:
                    lf.write(msg + "\n")
        except Exception:
            pass
        print(msg, file=sys.stderr)
        sys.exit(2)
    port = int(port)

    # Connect to backend proxy and forward between stdio and socket.
    try:
        if logpath:
            with open(logpath, 'a', encoding='utf-8') as lf:
                lf.write(f"wrapper pid={os.getpid()} connecting to {host}:{port}\n")
        with socket.create_connection((host, port)) as s:
            s.setblocking(True)
            # Forward stdin -> socket
            try:
                # Send any pre-read data from stdin to the socket
                while True:
                    data = sys.stdin.buffer.read(1024)
                    if not data:
                        break
                    s.sendall(data)
            except Exception as e:
                try:
                    if logpath:
                        with open(logpath, 'a', encoding='utf-8') as lf:
                            lf.write(f"stdin->socket error: {e}\n")
                except Exception:
                    pass

            # Now read from socket and write to stdout until closed
            try:
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            except Exception as e:
                try:
                    if logpath:
                        with open(logpath, 'a', encoding='utf-8') as lf:
                            lf.write(f"socket->stdout error: {e}\n")
                except Exception:
                    pass
    except Exception as e:
        try:
            if logpath:
                with open(logpath, 'a', encoding='utf-8') as lf:
                    lf.write(f"wrapper failed to connect: {e}\n")
        except Exception:
            pass
        # Re-raise so caller can observe failure on stderr
        raise


if __name__ == "__main__":
    main()
