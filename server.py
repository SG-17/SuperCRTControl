from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote
import socket
import os
import sys
import json
import re
import urllib.request
import urllib.error

HOST = "0.0.0.0"
PORT = 80   # Change if you have a conflict, you'll need to add :PORT on the end of any IP or mDNS address if not using port 80 (http://supercrt.local:8001 or http://192.158.1.251:8001)
DXP_TCP_PORT = 23
TCP_TIMEOUT = 2.0
MDNS_NAME = "supercrt"  # Allows you to use http://supercrt.local to access the site, you can change this ("" disables).
MDNS_TITLE = "Super CRT Control" 

ROOT = os.path.dirname(os.path.abspath(__file__))
ALIASES_FILE = os.path.join(ROOT, "aliases.json")
DONUTSHOP_FILE = os.path.join(ROOT, "donutshop.json")

_TLS_HANDSHAKE = 0x16
_PRESET_RE = re.compile(r"^\s*(\d+)\s*\.\s*$")


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


def load_donutshop():
    try:
        with open(DONUTSHOP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[DONUTSHOP] load error: {e}")
        return {}


def parse_preset(cmd: str):
    if not cmd:
        return None
    m = _PRESET_RE.match(cmd.strip())
    if not m:
        return None
    return int(m.group(1))


def donutshop_offset_for_ip(cfg: dict, ip: str):
    ip = normalize_ip(ip)
    for d in cfg.get("devices") or []:
        dip = normalize_ip(str(d.get("ip") or ""))
        if dip == ip:
            try:
                return int(d.get("offset") if d.get("offset") is not None else 0)
            except (TypeError, ValueError):
                return 0
    return None


def normalize_ip(ip: str) -> str:
    ip = (ip or "").strip()
    if ip.lower().startswith("http://"):
        ip = ip[7:]
    elif ip.lower().startswith("https://"):
        ip = ip[8:]
    return ip.split("/")[0].split(":")[0]


def svs_from_preset(offset: int, preset: int) -> int:
    if offset >= 100:
        return offset + preset
    return offset * 100 + preset


def _donutshop_hosts(cfg: dict):
    hosts = []
    for key in ("host", "fallback"):
        h = (cfg.get(key) or "").strip().rstrip("/")
        if h and h not in hosts:
            hosts.append(h)
    if not hosts:
        hosts.append("http://donutshop.local")
    return hosts


def _http_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post_donutshop_svs(svs: int, cfg: dict | None = None):
    cfg = cfg if cfg is not None else load_donutshop()
    timeout = float(cfg.get("timeout") or TCP_TIMEOUT)
    payload = f"plain=SVS NEW INPUT={svs}".encode("ascii")
    opener = _http_opener()
    last_error = "no host configured"
    for host in _donutshop_hosts(cfg):
        url = host.rstrip("/") + "/cmd"
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        print(f"[DONUTSHOP] POST {url}  SVS NEW INPUT={svs}")
        try:
            with opener.open(req, timeout=timeout) as resp:
                reply = resp.read().decode("utf-8", errors="replace")
                status = getattr(resp, "status", 200)
            extra = (" " + reply.strip()[:200]) if reply.strip() else ""
            print(f"[DONUTSHOP] {status}{extra}")
            return {"ok": True, "url": url, "svs": svs, "status": status, "response": reply}
        except urllib.error.HTTPError as e:
            if 200 <= e.code < 300:
                print(f"[DONUTSHOP] {e.code}")
                return {"ok": True, "url": url, "svs": svs, "status": e.code, "response": ""}
            last_error = f"HTTP {e.code} {e.reason}"
            print(f"[DONUTSHOP] FAIL {url}: {last_error}")
        except Exception as e:
            last_error = str(e)
            print(f"[DONUTSHOP] FAIL {url}: {last_error}")
    return {"ok": False, "svs": svs, "error": last_error}


def notify_donutshop(ip: str, cmd: str):
    cfg = load_donutshop()
    preset = parse_preset(cmd)
    if preset is None:
        return None
    if not os.path.isfile(DONUTSHOP_FILE):
        msg = f"missing {DONUTSHOP_FILE}"
        print(f"[DONUTSHOP] skipped: {msg}")
        return {"ok": False, "error": msg}
    if not cfg.get("enabled"):
        msg = f"disabled in {DONUTSHOP_FILE}"
        print(f"[DONUTSHOP] skipped: {msg}")
        return {"ok": False, "error": msg}
    offset = donutshop_offset_for_ip(cfg, ip)
    if offset is None:
        msg = f"no device map for {ip} (cmd={cmd!r})"
        print(f"[DONUTSHOP] {msg}")
        return {"ok": False, "error": msg, "ip": ip, "cmd": cmd}
    svs = svs_from_preset(offset, preset)
    result = post_donutshop_svs(svs, cfg)
    result["ip"] = ip
    result["preset"] = preset
    result["offset"] = offset
    return result


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
            ds = notify_donutshop(ip, cmd)
            row = {
                "ok": True,
                "ip": ip,
                "cmd": cmd,
                "transport": transport,
                "response": body or "ok",
            }
            if ds is not None:
                row["donutshop"] = ds
            results.append(row)
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
                ds = notify_donutshop(ip, cmd)
                if ds is None:
                    return self._reply(200, body if body else "ok")
                return self._reply_json(200, {
                    "extron": body if body else "ok",
                    "donutshop": ds,
                })
            except Exception as e:
                print(f"[API ERROR] {e}")
                return self._reply(502, f"proxy error: {e}")

        if path == "/api/aliases":
            return self._reply_json(200, {"aliases": load_aliases()})

        if path == "/api/donutshop":
            cfg = load_donutshop()
            cfg["_file"] = DONUTSHOP_FILE
            cfg["_exists"] = os.path.isfile(DONUTSHOP_FILE)
            return self._reply_json(200, cfg)

        if path == "/api/donutshop/test":
            qs = parse_qs(parsed.query)
            try:
                svs = int((qs.get("n") or ["1"])[0])
            except ValueError:
                return self._reply(400, "n must be an integer")
            result = post_donutshop_svs(svs)
            return self._reply_json(200 if result.get("ok") else 502, result)

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


def start_mdns(ip: str, port: int):
    name = (MDNS_NAME or "").strip().strip(".")
    if not name:
        return None
    host = f"{name}.local."
    title = (MDNS_TITLE or name).strip() or name

    try:
        from zeroconf import ServiceInfo, Zeroconf
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{title}._http._tcp.local.",
            addresses=[socket.inet_aton(ip)],
            port=port,
            properties={"path": "/", "alias": name},
            server=host,
        )
        zc = Zeroconf()
        zc.register_service(info)
        print(f"mDNS:      http://{name}.local:{port}/  (zeroconf)")
        return ("zeroconf", zc, info)
    except ImportError:
        pass
    except Exception as e:
        print(f"mDNS:      zeroconf failed ({e}), trying avahi")

    try:
        import subprocess
        proc = subprocess.Popen(
            ["avahi-publish", "-a", "-R", f"{name}.local", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"mDNS:      http://{name}.local:{port}/  (avahi-publish)")
        return ("avahi", proc, None)
    except FileNotFoundError:
        print(
            "mDNS:      not advertised. Install one of:\n"
            "           pip install zeroconf\n"
            "           sudo apt install avahi-utils"
        )
        return None
    except Exception as e:
        print(f"mDNS:      avahi-publish failed ({e})")
        return None


def stop_mdns(handle) -> None:
    if not handle:
        return
    kind, obj, extra = handle
    try:
        if kind == "zeroconf":
            obj.unregister_service(extra)
            obj.close()
        elif kind == "avahi" and obj.poll() is None:
            obj.terminate()
    except Exception:
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        sys.exit(
            f"Cannot bind {HOST}:{PORT} — {e}\n"
            f"Stop the other web server or change PORT."
        )

    lan = get_lan_ip()
    ds = load_donutshop()
    mdns = start_mdns(lan, PORT)
    print(f"Site root: {ROOT}")
    print(f"Aliases:   {ALIASES_FILE} exists={os.path.isfile(ALIASES_FILE)}")
    print(f"DonutShop: {DONUTSHOP_FILE} enabled={bool(ds.get('enabled'))} host={ds.get('host')}")
    print(f"Home:      http://{lan}:{PORT}/")
    print(f"API:       http://{lan}:{PORT}/api/cmd?ip=<ip>&c=<sis>&transport=tcp")
    print(f"Aliases:   http://{lan}:{PORT}/api/aliases")
    print(f"DonutShop: http://{lan}:{PORT}/api/donutshop")
    print(f"Example:   http://{lan}:{PORT}/ps1")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        stop_mdns(mdns)
