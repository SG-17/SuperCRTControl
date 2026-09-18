from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote
import socket
import os
import sys
import json

HOST = "0.0.0.0"
PORT = 8001
DXP_TCP_PORT = 23
TCP_TIMEOUT = 2.0

ROOT = os.path.dirname(os.path.abspath(__file__))
ALIASES_FILE = os.path.join(ROOT, "aliases.json")

_TLS_HANDSHAKE = 0x16


def send_sis_tcp(ip: str, cmd: str) -> str:
    data = b""
    with socket.create_connection((ip, DXP_TCP_PORT), timeout=TCP_TIMEOUT) as sock:
        sock.settimeout(TCP_TIMEOUT)
        sock.sendall(cmd.encode("ascii", errors="ignore"))
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                sock.settimeout(0.2)
        except socket.timeout:
            pass
    return data.decode("utf-8", errors="replace")


def send_sis_http(ip: str, cmd: str) -> str:
    import urllib.request
    url = f"http://{ip}/?cmd={quote(cmd, safe='')}"
    with urllib.request.urlopen(url, timeout=TCP_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_aliases():
    try:
        with open(ALIASES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k).strip().lower().lstrip("/"): v for k, v in data.items()}
    except FileNotFoundError:
        print(f"[ALIASES] missing file: {ALIASES_FILE}")
        return {}
    except Exception as e:
        print(f"[ALIASES] load error: {e}")
        return {}


def run_alias_actions(actions):
    results = []
    for a in actions or []:
        ip = (a.get("ip") or "").strip()
        cmd = (a.get("cmd") or "").strip()
        transport = (a.get("transport") or "http").lower()
        if not ip or not cmd:
            results.append({"ok": False, "error": "missing ip or cmd", "action": a})
            continue
        try:
            if transport == "http":
                body = send_sis_http(ip, cmd)
            else:
                body = send_sis_tcp(ip, cmd)
            results.append({
                "ok": True,
                "ip": ip,
                "cmd": cmd,
                "transport": transport,
                "response": body or "ok",
            })
            print(f"[ALIAS] OK {transport} {ip} {cmd!r}")
        except Exception as e:
            results.append({
                "ok": False,
                "ip": ip,
                "cmd": cmd,
                "transport": transport,
                "error": str(e),
            })
            print(f"[ALIAS] FAIL {transport} {ip} {cmd!r}: {e}")
    return results


def handle_alias(name):
    aliases = load_aliases()
    key = name.strip().lower().lstrip("/")
    if key not in aliases:
        return None
    entry = aliases[key]
    if isinstance(entry, list):
        actions = entry
        description = key
    elif isinstance(entry, dict):
        actions = entry.get("actions") or []
        description = entry.get("description") or key
    else:
        return {"ok": False, "error": "invalid alias entry", "alias": key}
    results = run_alias_actions(actions)
    ok = bool(results) and all(r.get("ok") for r in results)
    return {
        "ok": ok,
        "alias": key,
        "description": description,
        "results": results,
    }


def _is_noise_log(text: str) -> bool:
    t = text.lower()
    if "bad request version" in t:
        return True
    if "code 400" in t and "message bad request" in t:
        return True
    if "\x16" in text or "\x13\x01" in text:
        return True
    return False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
        except TimeoutError:
            self.close_connection = True
            return
        except Exception:
            self.close_connection = True
            return

        if not self.raw_requestline:
            self.close_connection = True
            return

        if self.raw_requestline[0] == _TLS_HANDSHAKE:
            self.close_connection = True
            return

        if len(self.raw_requestline) > 65536:
            self.requestline = ""
            self.request_version = ""
            self.command = ""
            self.send_error(414)
            return

        if not self.parse_request():
            return

        mname = "do_" + self.command
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%r)" % self.command)
            return
        getattr(self, mname)()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        print(f"[REQ] path={path!r}")

        if path in ("/api/cmd", "/cmd"):
            qs = parse_qs(parsed.query)
            ip = (qs.get("ip") or [""])[0].strip()
            cmd = unquote((qs.get("c") or [""])[0])
            transport = ((qs.get("transport") or ["tcp"])[0]).lower()
            print(f"[API] ip={ip!r} cmd={cmd!r} transport={transport!r}")
            if not ip or cmd == "":
                return self._reply(400, "missing ip or c")
            try:
                if transport == "http":
                    body = send_sis_http(ip, cmd)
                else:
                    body = send_sis_tcp(ip, cmd)
                return self._reply(200, body if body else "ok")
            except Exception as e:
                print(f"[API ERROR] {e}")
                return self._reply(502, f"proxy error: {e}")

        if path == "/api/aliases":
            return self._reply_json(200, {"aliases": load_aliases()})

        if path != "/" and not path.startswith("/api") and not path.startswith("/cmd"):
            seg = path.lstrip("/")
            if seg and "/" not in seg and "." not in seg:
                print(f"[ALIAS LOOKUP] {seg!r} file={ALIASES_FILE}")
                result = handle_alias(seg)
                if result is not None:
                    code = 200 if result.get("ok") else 502
                    return self._reply_json(code, result)
                print(f"[ALIAS MISS] no key {seg!r}; known={list(load_aliases().keys())}")

        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _reply(self, code: int, text: str):
        data = text.encode("utf-8", errors="replace")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _reply_json(self, code: int, obj):
        data = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        try:
            text = fmt % args
        except Exception:
            text = str(fmt)
        if _is_noise_log(text):
            return
        print("%s - %s" % (self.address_string(), text))

    def log_error(self, fmt, *args):
        try:
            text = fmt % args
        except Exception:
            text = str(fmt)
        if _is_noise_log(text):
            return
        self.log_message(fmt, *args)


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    os.chdir(ROOT)
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        sys.exit(
            f"Cannot bind {HOST}:{PORT} — {e}\n"
            f"Stop the other web server or change PORT."
        )

    print(f"Site root: {ROOT}")
    print(f"Aliases:   {ALIASES_FILE} exists={os.path.isfile(ALIASES_FILE)}")
    print(f"Home:      http://{get_lan_ip()}:{PORT}/")
    print(f"API:       http://{get_lan_ip()}:{PORT}/api/cmd?ip=<ip>&c=<sis>&transport=tcp")
    print(f"Aliases:   http://{get_lan_ip()}:{PORT}/api/aliases")
    print(f"Example:   http://{get_lan_ip()}:{PORT}/ps1")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
