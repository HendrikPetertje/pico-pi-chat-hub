import socket
import json
import uselect
import uos
import time


HEADERS_200_HTML = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Connection: close\r\n"
)

HEADERS_200_JSON = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: application/json\r\n"
    "Connection: close\r\n"
)

HEADERS_400 = (
    "HTTP/1.1 400 Bad Request\r\n"
    "Content-Type: application/json\r\n"
    "Connection: close\r\n"
)

HEADERS_404 = (
    "HTTP/1.1 404 Not Found\r\n"
    "Content-Type: text/plain\r\n"
    "Connection: close\r\n"
)

HEADERS_405 = (
    "HTTP/1.1 405 Method Not Allowed\r\n"
    "Content-Type: text/plain\r\n"
    "Connection: close\r\n"
)

HEADERS_302 = (
    "HTTP/1.1 302 Found\r\n"
    "Content-Type: text/plain\r\n"
    "Location: http://192.168.4.1/\r\n"
    "Connection: close\r\n"
)

MAX_HEADER_SIZE = 4096   # bytes; cap unbounded header reads
MAX_BODY_SIZE   = 1024   # bytes; cap POST body
CONN_TIMEOUT    = 15     # seconds; drop slow/hung clients


def _send(conn, headers, body):
    if isinstance(body, str):
        body = body.encode()
    response = (headers + "Content-Length: {}\r\n\r\n".format(len(body))).encode() + body
    conn.sendall(response)


def _parse_buf(buf):
    """Parse a complete HTTP request from a buffer. Returns (method, path, body) or (None, None, None)."""
    if b"\r\n\r\n" not in buf:
        return None, None, None

    header_part, _, rest = buf.partition(b"\r\n\r\n")
    lines = header_part.decode().split("\r\n")
    request_line = lines[0].split()

    if len(request_line) < 2:
        return None, None, b""

    method = request_line[0]
    path = request_line[1].split("?")[0]

    content_length = 0
    for line in lines[1:]:
        if line.lower().startswith("content-length:"):
            try:
                content_length = min(int(line.split(":", 1)[1].strip()), MAX_BODY_SIZE)
            except ValueError:
                pass

    if len(rest) < content_length:
        return None, None, None  # body not yet fully received

    return method, path, rest[:content_length]


class HTTPServer:
    def __init__(self, messages, add_message):
        self.messages = messages
        self.add_message = add_message

    def _dispatch(self, conn, method, path, body):
        print(method, path)

        if path in ("/", "/index.html"):
            if method != "GET":
                _send(conn, HEADERS_405, "Method Not Allowed")
            else:
                self._serve_index(conn)

        elif path == "/messages":
            if method == "GET":
                self._get_messages(conn)
            elif method == "POST":
                self._post_message(conn, body)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        else:
            # Redirect anything unknown (captive portal probes) to root
            _send(conn, HEADERS_302, "Redirecting...")

    def _serve_index(self, conn):
        try:
            size = uos.stat("index.html")[6]
            header = (HEADERS_200_HTML + "Content-Length: {}\r\n\r\n".format(size)).encode()
            conn.sendall(header)
            with open("index.html", "rb") as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    conn.sendall(chunk)
        except OSError:
            _send(conn, HEADERS_404, "index.html not found")

    def _get_messages(self, conn):
        _send(conn, HEADERS_200_JSON, json.dumps(self.messages))

    def _post_message(self, conn, body):
        try:
            payload = json.loads(body.decode())
            username = str(payload.get("u", "")).strip()
            text = str(payload.get("message", "")).strip()
            if not username or not text:
                _send(conn, HEADERS_400, '{"error":"u and message are required"}')
                return
            self.add_message(username, text)
            _send(conn, HEADERS_200_JSON, '{"ok":true}')
        except (ValueError, KeyError) as e:
            _send(conn, HEADERS_400, json.dumps({"error": "invalid JSON: {}".format(e)}))

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", 80))
        srv.listen(5)
        srv.setblocking(False)

        poll = uselect.poll()
        poll.register(srv, uselect.POLLIN)

        # clients: conn -> (recv_buf, opened_at)
        clients = {}

        print("HTTP server running")

        while True:
            try:
                events = poll.poll(1000)
            except Exception as e:
                print("poll error:", e)
                continue

            now = time.time()

            for obj, event in events:
                if obj is srv:
                    # New incoming connection
                    try:
                        conn, addr = srv.accept()
                        conn.setblocking(False)
                        poll.register(conn, uselect.POLLIN)
                        clients[conn] = (b"", now)
                    except Exception as e:
                        print("accept error:", e)
                else:
                    conn = obj
                    if conn not in clients:
                        poll.unregister(conn)
                        conn.close()
                        continue

                    buf, opened_at = clients[conn]

                    # Read available data
                    try:
                        chunk = conn.recv(256)
                    except OSError:
                        chunk = b""

                    if not chunk:
                        # Client disconnected
                        poll.unregister(conn)
                        del clients[conn]
                        conn.close()
                        continue

                    buf += chunk
                    if len(buf) > MAX_HEADER_SIZE + MAX_BODY_SIZE:
                        # Request too large
                        poll.unregister(conn)
                        del clients[conn]
                        conn.close()
                        continue

                    method, path, body = _parse_buf(buf)

                    if method is None and path is None and body is None:
                        # Incomplete request, keep buffering
                        clients[conn] = (buf, opened_at)
                        continue

                    # Complete request — dispatch and close
                    poll.unregister(conn)
                    del clients[conn]
                    try:
                        if method is None:
                            _send(conn, HEADERS_400, '{"error":"bad request"}')
                        else:
                            self._dispatch(conn, method, path, body)
                    except Exception as e:
                        print("Handler error:", e)
                    finally:
                        conn.close()

            # Evict timed-out connections
            now = time.time()
            stale = [c for c, (_, t) in clients.items() if now - t > CONN_TIMEOUT]
            for conn in stale:
                poll.unregister(conn)
                del clients[conn]
                conn.close()
