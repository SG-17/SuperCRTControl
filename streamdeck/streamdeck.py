from __future__ import annotations

import io
import os
import sys
import threading
import time

import requests
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

try:
    from StreamDeck.Transport.Transport import TransportError
except Exception:
    TransportError = OSError

from streamdeck_config import (
    HOME_PAGE,
    IDLE_SLEEP_SECONDS,
    ORIENTATION,
    PAGES,
    PRESS_FLASH_SECONDS,
    PROCESS_REFRESH_SECONDS,
    SCC,
    WAKE_BRIGHTNESS,
)

ORIENTATION_IMAGE = None
POLL_SLEEP = 0.25
RECONNECT_SECONDS = 2.0
OPEN_SETTLE_SECONDS = 0.5
USB_RESET_SETTLE_SECONDS = 2.5
HEARTBEAT_STALE_SECONDS = 45

ELGATO_VID = "0fd9"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamdeck.log")
_log_fp = None

CURRENT_PAGE = HOME_PAGE
DECK_COLS = 5
DECK_ROWS = 3
_last_activity = time.monotonic()
_asleep = False
_lock = threading.Lock()
_process_started = time.monotonic()
_heartbeat = time.monotonic()
_restarting = False
_active_deck = None
_icon_cache: dict[str, bytes] = {}

def deck_orientation() -> int:
    try:
        angle = int(ORIENTATION) % 360
    except (TypeError, ValueError):
        return 0
    if angle not in (0, 90, 180, 270):
        return 0
    return angle


def visual_grid() -> tuple[int, int]:
    if deck_orientation() in (90, 270):
        return DECK_ROWS, DECK_COLS
    return DECK_COLS, DECK_ROWS


def visual_to_hw(visual: int) -> int:
    angle = deck_orientation()
    cols, rows = visual_grid()
    if visual < 0 or visual >= cols * rows:
        return visual
    vr, vc = divmod(visual, cols)
    if angle == 0:
        hr, hc = vr, vc
    elif angle == 90:
        hr, hc = DECK_ROWS - 1 - vc, vr
    elif angle == 180:
        hr, hc = DECK_ROWS - 1 - vr, DECK_COLS - 1 - vc
    else:
        hr, hc = vc, DECK_COLS - 1 - vr
    return hr * DECK_COLS + hc


def hw_to_visual(hw: int) -> int:
    angle = deck_orientation()
    hr, hc = divmod(int(hw), DECK_COLS)
    if angle == 0:
        vr, vc = hr, hc
        cols = DECK_COLS
    elif angle == 90:
        vr, vc = hc, DECK_ROWS - 1 - hr
        cols = DECK_ROWS
    elif angle == 180:
        vr, vc = DECK_ROWS - 1 - hr, DECK_COLS - 1 - hc
        cols = DECK_COLS
    else:
        vr, vc = DECK_COLS - 1 - hc, hr
        cols = DECK_ROWS
    return vr * cols + vc


def touch_activity() -> None:
    global _last_activity
    _last_activity = time.monotonic()


def beat() -> None:
    global _heartbeat
    _heartbeat = time.monotonic()


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        try:
            return bool(self.streams and self.streams[0].isatty())
        except Exception:
            return False


def start_log_file() -> None:
    global _log_fp
    path = (LOG_FILE or "").strip()
    if not path:
        return
    try:
        _log_fp = open(path, "a", encoding="utf-8", buffering=1)
    except Exception as e:
        print(f"Could not open log file {path}: {e}")
        return
    sys.stdout = _Tee(sys.__stdout__, _log_fp)
    sys.stderr = _Tee(sys.__stderr__, _log_fp)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f" {stamp} pid={os.getpid()} ")
    print(f"Logging to {path}")


def iter_elgato_usb():
    root = "/sys/bus/usb/devices"
    if not os.path.isdir(root):
        return
    try:
        names = os.listdir(root)
    except OSError:
        return
    for name in names:
        path = os.path.join(root, name)
        try:
            with open(os.path.join(path, "idVendor"), encoding="ascii") as f:
                vendor = f.read().strip().lower()
        except OSError:
            continue
        if vendor == ELGATO_VID:
            yield path


def _sysfs_write(path: str, value: str) -> bool:
    try:
        with open(path, "w", encoding="ascii") as f:
            f.write(value)
        return True
    except OSError as e:
        print(f"sysfs write {path}={value!r} failed ({e})")
        return False


def disable_elgato_autosuspend() -> None:
    for path in iter_elgato_usb():
        ctrl = os.path.join(path, "power", "control")
        auto = os.path.join(path, "power", "autosuspend")
        auto_d = os.path.join(path, "power", "autosuspend_delay_ms")
        if os.path.exists(ctrl) and _sysfs_write(ctrl, "on"):
            print(f"USB autosuspend off {path}")
        if os.path.exists(auto):
            _sysfs_write(auto, "-1")
        if os.path.exists(auto_d):
            _sysfs_write(auto_d, "-1")


def rebind_elgato_hid() -> bool:
    ok = False
    for path in iter_elgato_usb():
        try:
            names = os.listdir(path)
        except OSError:
            continue
        for name in names:
            if ":" not in name:
                continue
            iface = os.path.join(path, name)
            link = os.path.join(iface, "driver")
            if not os.path.islink(link):
                continue
            driver = os.path.basename(os.path.realpath(link))
            unbind = f"/sys/bus/usb/drivers/{driver}/unbind"
            bind = f"/sys/bus/usb/drivers/{driver}/bind"
            print(f"HID rebind {name} ({driver})")
            _sysfs_write(unbind, name)
            time.sleep(0.4)
            if _sysfs_write(bind, name):
                ok = True
    if ok:
        time.sleep(1.0)
        disable_elgato_autosuspend()
    return ok


def parent_usb_path(path: str) -> str | None:
    name = os.path.basename(path)
    if "." in name:
        parent = name.rsplit(".", 1)[0]
        return os.path.join(os.path.dirname(path), parent)
    if "-" in name:
        bus, _, port = name.partition("-")
        if "." in port:
            parent = bus + "-" + port.rsplit(".", 1)[0]
            return os.path.join(os.path.dirname(path), parent)
    return None


def reset_parent_hub() -> bool:
    parents = []
    for path in iter_elgato_usb():
        parent = parent_usb_path(path)
        if parent and parent not in parents:
            parents.append(parent)
    if not parents:
        print("USB parent hub: none found")
        return False
    ok = False
    for parent in parents:
        auth = os.path.join(parent, "authorized")
        if not os.path.exists(auth):
            print(f"USB parent hub: no authorized at {parent}")
            continue
        print(f"USB parent hub reset {parent}")
        if not _sysfs_write(auth, "0"):
            continue
        time.sleep(1.0)
        if _sysfs_write(auth, "1"):
            ok = True
    if ok:
        time.sleep(USB_RESET_SETTLE_SECONDS)
        disable_elgato_autosuspend()
    return ok


def recover_elgato_usb(fail_count: int) -> None:
    disable_elgato_autosuspend()
    if fail_count == 2:
        print("Open failed - rebind usbhid")
        rebind_elgato_hid()
    elif fail_count == 5:
        print("Open failed - reset parent USB hub")
        reset_parent_hub()
    elif fail_count >= 8 and fail_count % 8 == 0:
        print("Open still failing - unplug the Stream Deck USB cable")


def restore_state_from_env() -> None:
    global CURRENT_PAGE, _asleep
    page = os.environ.get("SUPERCRT_DECK_PAGE", "")
    if page in PAGES:
        CURRENT_PAGE = page
    _asleep = os.environ.get("SUPERCRT_DECK_ASLEEP") == "1"


def apply_sleep_display(deck) -> None:
    try:
        with deck:
            deck.set_brightness(0)
    except Exception as e:
        print(f"sleep brightness: {e}")
    clear_all_keys(deck)


def self_restart(deck=None, reason: str = "scheduled") -> None:
    global _restarting
    if _restarting:
        return
    _restarting = True
    print(f"Self-restart ({reason}).")

    env = os.environ.copy()
    env["SUPERCRT_DECK_PAGE"] = CURRENT_PAGE
    env["SUPERCRT_DECK_ASLEEP"] = "1" if _asleep else "0"

    def _close() -> None:
        close_deck(deck)

    closer = threading.Thread(target=_close, name="deck-close", daemon=True)
    closer.start()
    closer.join(timeout=2.0)
    if os.environ.get("INVOCATION_ID"):
        print("Exiting for systemd restart")
        os._exit(0)

    python = sys.executable or "python3"
    argv = [python] + sys.argv
    try:
        os.execve(python, argv, env)
    except Exception as e:
        print(f"execve failed: {e}")
        os._exit(1)


def start_watchdog() -> None:

    def _run() -> None:
        while True:
            time.sleep(5)
            if _restarting:
                return
            now = time.monotonic()
            if PROCESS_REFRESH_SECONDS and (now - _process_started) >= PROCESS_REFRESH_SECONDS:
                self_restart(_active_deck, "hourly refresh")
                return
            if (now - _heartbeat) >= HEARTBEAT_STALE_SECONDS:
                self_restart(_active_deck, "HID heartbeat stale")
                return

    threading.Thread(target=_run, name="deck-watchdog", daemon=True).start()


def image_orientation() -> int:
    if ORIENTATION_IMAGE is None:
        return deck_orientation()
    try:
        angle = int(ORIENTATION_IMAGE) % 360
    except (TypeError, ValueError):
        return deck_orientation()
    if angle not in (0, 90, 180, 270):
        return deck_orientation()
    return angle


def _compose_key_image(deck, image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    if hasattr(PILHelper, "create_scaled_key_image"):
        return PILHelper.create_scaled_key_image(deck, image)
    if hasattr(PILHelper, "create_key_image"):
        canvas = PILHelper.create_key_image(deck)
    else:
        canvas = PILHelper.create_image(deck)
    fitted = image.copy()
    fitted.thumbnail(canvas.size)
    canvas.paste(
        fitted,
        (
            (canvas.width - fitted.width) // 2,
            (canvas.height - fitted.height) // 2,
        ),
    )
    return canvas


def _pil_to_native(deck, image: Image.Image):
    image_formatted = _compose_key_image(deck, image)
    angle = image_orientation()
    if angle:
        image_formatted = image_formatted.rotate(angle, expand=False)
    if hasattr(PILHelper, "to_native_key_format"):
        return PILHelper.to_native_key_format(deck, image_formatted)
    return PILHelper.to_native_format(deck, image_formatted)


def set_key_solid(deck, key: int, color: tuple[int, int, int] = (255, 255, 255)) -> None:
    try:
        w, h = deck.key_image_format()["size"]
    except Exception:
        w, h = 72, 72
    try:
        raw = _pil_to_native(deck, Image.new("RGB", (w, h), color))
        with deck:
            deck.set_key_image(key, raw)
    except Exception as e:
        print(f"flash key {key}: {e}")


def _icon_cache_key(icon_url: str) -> str:
    return f"{image_orientation()}|{icon_url}"


def flash_key(deck, key: int, icon_url: str | None = None) -> None:
    if PRESS_FLASH_SECONDS <= 0:
        return
    set_key_solid(deck, key, (255, 255, 255))
    time.sleep(PRESS_FLASH_SECONDS)
    if icon_url:
        set_key_image_from_url(deck, key, icon_url)


def set_key_image_from_url(deck, key: int, icon_url: str) -> None:
    cache_key = _icon_cache_key(icon_url)
    raw_bytes = _icon_cache.get(cache_key)
    if raw_bytes is None:
        try:
            response = requests.get(icon_url, timeout=4)
            if response.status_code != 200:
                print(f"Icon HTTP {response.status_code} for key {key}: {icon_url}")
                return
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            raw_bytes = _pil_to_native(deck, image)
            _icon_cache[cache_key] = raw_bytes
        except Exception as e:
            print(f"Network/icon error key {key}: {e}")
            return
    try:
        with deck:
            deck.set_key_image(key, raw_bytes)
    except Exception as e:
        print(f"Network/icon error key {key}: {e}")


def clear_all_keys(deck) -> None:
    try:
        with deck:
            for key in range(deck.key_count()):
                deck.set_key_image(key, None)
    except Exception as e:
        print(f"clear_all_keys: {e}")


def render_current_page(deck) -> None:
    print(f"\nLoading page: {CURRENT_PAGE} ")
    try:
        with deck:
            deck.set_brightness(WAKE_BRIGHTNESS)
    except Exception as e:
        print(f"reset/brightness: {e}")

    clear_all_keys(deck)
    page_data = PAGES.get(CURRENT_PAGE, {})
    for visual_key, data in page_data.items():
        if "icon_url" in data:
            set_key_image_from_url(deck, visual_to_hw(int(visual_key)), data["icon_url"])
    print("Page rendered")


def go_to_sleep(deck) -> None:
    global _asleep
    with _lock:
        if _asleep:
            return
        print("Idle timeout - Stream Deck sleep")
        apply_sleep_display(deck)
        _asleep = True


def wake_up(deck) -> None:
    global _asleep
    with _lock:
        if not _asleep:
            touch_activity()
            return
        print("Waking")
        _asleep = False
        touch_activity()
        render_current_page(deck)


def button_callback(deck, key: int, state: bool) -> None:
    global CURRENT_PAGE

    if not state:
        return

    if _asleep:
        wake_up(deck)
        return

    touch_activity()

    visual_key = hw_to_visual(key)
    current_page_macros = PAGES.get(CURRENT_PAGE, {})
    if visual_key not in current_page_macros:
        return

    button_data = current_page_macros[visual_key]
    flash_key(deck, key, button_data.get("icon_url"))

    if "url" in button_data:
        url = button_data["url"]
        print(f"[{CURRENT_PAGE}] GET {url}")
        try:
            response = requests.get(url, timeout=3)
            print(f"Response: {response.status_code}")
        except Exception as e:
            print(f"HTTP failed: {e}")

    if "target_page" in button_data:
        next_page = button_data["target_page"]
        if next_page in PAGES:
            CURRENT_PAGE = next_page
            render_current_page(deck)
        else:
            print(f"Unknown target_page: {next_page}")


def close_deck(deck) -> None:
    if deck is None:
        return
    try:
        deck.set_key_callback(None)
    except Exception:
        pass
    try:
        deck.close()
    except Exception:
        pass


def try_open_deck():
    try:
        found = DeviceManager().enumerate()
    except Exception as e:
        print(f"enumerate failed: {e}")
        return None
    if not found:
        return None
    deck = found[0]
    try:
        deck.open()
        time.sleep(OPEN_SETTLE_SECONDS)
        try:
            deck.set_brightness(WAKE_BRIGHTNESS)
            kind = deck.deck_type()
            serial = deck.get_serial_number()
        except Exception as e:
            print(f"open incomplete: {e}")
            try:
                deck.close()
            except Exception:
                pass
            return None
        print(f"Opened: {kind} serial={serial}")
        return deck
    except Exception as e:
        print(f"open failed: {e}")
        try:
            deck.close()
        except Exception:
            pass
        return None


def deck_still_connected(deck) -> bool:
    try:
        with deck:
            deck.get_serial_number()
        return True
    except (TransportError, OSError, Exception):
        return False


def main() -> None:
    global _asleep, _active_deck

    start_log_file()
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamdeck_config.py")
    print(f"Config:    {cfg_path}")
    print(f"SCC host:  {SCC}")
    cols, rows = visual_grid()
    print(
        f"Orientation: {deck_orientation()}°  icons {image_orientation()}°  "
        f"visual grid {cols}×{rows}"
    )
    restore_state_from_env()
    beat()
    start_watchdog()

    print(f"Idle sleep after {IDLE_SLEEP_SECONDS}s ({IDLE_SLEEP_SECONDS // 60} min)")
    if PROCESS_REFRESH_SECONDS:
        print(f"Process refresh every {PROCESS_REFRESH_SECONDS}s ({PROCESS_REFRESH_SECONDS // 60} min)")
    print("Waiting for a USB Stream Deck (will retry if unplugged).")
    disable_elgato_autosuspend()

    first_open = True
    open_fails = 0
    try:
        while True:
            deck = try_open_deck()
            if deck is None:
                open_fails += 1
                recover_elgato_usb(open_fails)
                wait = 8.0 if open_fails >= 8 else RECONNECT_SECONDS
                time.sleep(wait)
                beat()
                continue
            open_fails = 0
            disable_elgato_autosuspend()

            resume_sleep = first_open and _asleep
            first_open = False
            _active_deck = deck
            beat()

            if resume_sleep:
                print("Restored asleep after refresh")
                apply_sleep_display(deck)
            else:
                _asleep = False
                touch_activity()
                render_current_page(deck)

            deck.set_key_callback(button_callback)
            print("Super CRT Stream Deck Remote active.")

            try:
                while True:
                    time.sleep(POLL_SLEEP)
                    beat()
                    if PROCESS_REFRESH_SECONDS and (
                        time.monotonic() - _process_started
                    ) >= PROCESS_REFRESH_SECONDS:
                        self_restart(deck, "hourly refresh")
                        return
                    if not deck_still_connected(deck):
                        print("Stream Deck disconnected - waiting to plug it back in.")
                        break
                    if not _asleep and (time.monotonic() - _last_activity) >= IDLE_SLEEP_SECONDS:
                        go_to_sleep(deck)
            except KeyboardInterrupt:
                print("\nStopping.")
                close_deck(deck)
                return
            except (TransportError, OSError) as e:
                print(f"Stream Deck USB error: {e}")
            finally:
                _active_deck = None
                if not _restarting:
                    close_deck(deck)
    except KeyboardInterrupt:
        print("\nStopping.")


if __name__ == "__main__":
    main()
