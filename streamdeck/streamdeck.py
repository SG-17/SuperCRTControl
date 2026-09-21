from __future__ import annotations

import io
import os
import sys
import threading
import time
from typing import Any

import requests
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

try:
    from StreamDeck.Transport.Transport import TransportError
except Exception:
    TransportError = OSError

# Config — put your Super CRT-Control web server IP:PORT/IP/mDNS adddress below

SCC = "http://192.168.1.251"

IDLE_SLEEP_SECONDS = 1 * 60          # How long until the Deck sleeps, set to 60 seconds
WAKE_BRIGHTNESS = 60                 # How bright the Deck's buttons are, set between 0–100
POLL_SLEEP = 0.25
RECONNECT_SECONDS = 2.0
OPEN_SETTLE_SECONDS = 0.5
USB_RESET_SETTLE_SECONDS = 2.5
ELGATO_VID = "0fd9"
PROCESS_REFRESH_SECONDS = 60 * 60    # How often the program restarts itself, set to 60 minutes
HEARTBEAT_STALE_SECONDS = 45
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamdeck.log")
_log_fp = None

CURRENT_PAGE = "HOME"
_last_activity = time.monotonic()
_asleep = False
_lock = threading.Lock()
_process_started = time.monotonic()
_heartbeat = time.monotonic()
_restarting = False
_active_deck = None

# Pages: key index 0–14 (Stream Deck MK.2 = 15 keys)
# Can trigger a url, load a new page of buttons, or both

PAGES: dict[str, dict[int, dict[str, Any]]] = {
    "HOME": {
        0: {
            "label": "PlayStation 1",
            "icon_url": f"{SCC}/images/deck/ps1.png",
            "url": f"{SCC}/ps1",
        },
        1: {
            "label": "PlayStation 2",
            "icon_url": f"{SCC}/images/deck/ps2.png",
            "target_page": "PS2_GAMES",
        },
        2: {
            "label": "PlayStation 3",
            "icon_url": f"{SCC}/images/deck/ps3.png",
            "url": f"{SCC}/ps3",
        },
        3: {
            "label": "Nintendo Entertainment System",
            "icon_url": f"{SCC}/images/deck/nes.png",
            "url": f"{SCC}/nes",
        },
        4: {
            "label": "Super Nintendo",
            "icon_url": f"{SCC}/images/deck/snes.png",
            "url": f"{SCC}/snes",
        },
        5: {
            "label": "Nintendo 64",
            "icon_url": f"{SCC}/images/deck/n64.png",
            "url": f"{SCC}/n64",
        },
        6: {
            "label": "GameCube",
            "icon_url": f"{SCC}/images/deck/gamecube.png",
            "url": f"{SCC}/gamecube",
        },
        7: {
            "label": "Wii",
            "icon_url": f"{SCC}/images/deck/wii.png",
            "url": f"{SCC}/wii",
        },
        8: {
            "label": "Super Game Boy",
            "icon_url": f"{SCC}/images/deck/sgb.png",
            "url": f"{SCC}/sgb",
        },
        9: {
            "label": "Game Boy Interface",
            "icon_url": f"{SCC}/images/deck/gbi.png",
            "url": f"{SCC}/gbi",
        },
        10: {
            "label": "Sega Genesis",
            "icon_url": f"{SCC}/images/deck/genesis.png",
            "url": f"{SCC}/gen",
        },
        11: {
            "label": "VCR",
            "icon_url": f"{SCC}/images/deck/vhs.png",
            "url": f"{SCC}/vhs",
        },
        12: {
            "label": "TV Games",
            "icon_url": f"{SCC}/images/deck/tvgames.png",
            "url": f"{SCC}/tvgames",
        },
        13: {
            "label": "HDMI",
            "icon_url": f"{SCC}/images/deck/hdmi.png",
            "target_page": "HDMI",
        },
        14: {
            "label": "Reset",
            "icon_url": f"{SCC}/images/deck/reset.png",
            "url": f"{SCC}/reset",
        },
    },
    "PS2_GAMES": {
        0: {
            "label": "PlayStation 2",
            "icon_url": f"{SCC}/images/deck/ps2.png",
            "url": f"{SCC}/ps2",
        },
        1: {
            "label": "Godzilla Save the Earth",
            "icon_url": f"{SCC}/images/deck/ps2/godzillaste.png",
            "url": f"{SCC}/gste",
        },
        2: {
            "label": "King Kong",
            "icon_url": f"{SCC}/images/deck/ps2/kong.png",
            "url": f"{SCC}/kong",
        },
        3: {
            "label": "SOCOM Combined Assault",
            "icon_url": f"{SCC}/images/deck/ps2/socomca.png",
            "url": f"{SCC}/socomca",
        },
        4: {
            "label": "Star Wars Battlefront",
            "icon_url": f"{SCC}/images/deck/ps2/swbf.png",
            "url": f"{SCC}/swbf",
        },
        5: {
            "label": "Star Wars Battlefront II",
            "icon_url": f"{SCC}/images/deck/ps2/swbf2.png",
            "url": f"{SCC}/swbf2",
        },
        13: {
            "label": "Main Menu",
            "icon_url": f"{SCC}/images/deck/home.png",
            "target_page": "HOME",
        },
        14: {
            "label": "Reset",
            "icon_url": f"{SCC}/images/deck/reset.png",
            "url": f"{SCC}/reset",
        },
    },
    "HDMI": {
        0: {
            "label": "PlayStation 3",
            "icon_url": f"{SCC}/images/deck/hdmi/ps3.png",
            "url": f"{SCC}/ps3hd",
        },
        1: {
            "label": "PlayStation 4",
            "icon_url": f"{SCC}/images/deck/hdmi/ps4.png",
            "url": f"{SCC}/ps4",
        },
        2: {
            "label": "PlayStation TV",
            "icon_url": f"{SCC}/images/deck/hdmi/pstv.png",
            "url": f"{SCC}/pstv",
        },
        3: {
            "label": "PlayStation 5",
            "icon_url": f"{SCC}/images/deck/hdmi/ps5.png",
            "url": f"{SCC}/ps5",
        },
        4: {
            "label": "Xbox 360",
            "icon_url": f"{SCC}/images/deck/hdmi/360.png",
            "url": f"{SCC}/360",
        },
        5: {
            "label": "Xbox Series X",
            "icon_url": f"{SCC}/images/deck/hdmi/xsx.png",
            "url": f"{SCC}/xsx",
        },
        6: {
            "label": "GameCube",
            "icon_url": f"{SCC}/images/deck/hdmi/gamecube.png",
            "url": f"{SCC}/gamecube",
        },
        7: {
            "label": "Game Boy Interface",
            "icon_url": f"{SCC}/images/deck/hdmi/gbi.png",
            "url": f"{SCC}/gbi",
        },
        8: {
            "label": "Nintendo Switch",
            "icon_url": f"{SCC}/images/deck/hdmi/switch.png",
            "url": f"{SCC}/nsw",
        },
        9: {
            "label": "Nintendo Switch 2",
            "icon_url": f"{SCC}/images/deck/hdmi/switch2.png",
            "url": f"{SCC}/nsw2",
        },
        10: {
            "label": "RetroTink 4K Pro",
            "icon_url": f"{SCC}/images/deck/hdmi/rt4kpro.png",
            "url": f"{SCC}/tink",
        },
        13: {
            "label": "Main Menu",
            "icon_url": f"{SCC}/images/deck/home.png",
            "target_page": "HOME",
        },
        14: {
            "label": "Reset",
            "icon_url": f"{SCC}/images/deck/reset.png",
            "url": f"{SCC}/reset",
        },
    },
}

# Do not touch anything below this line

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
    print(f"----- {stamp} pid={os.getpid()} -----")
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


def set_elgato_authorized(value: str) -> bool:
    found = list(iter_elgato_usb())
    if not found:
        print(f"USB authorized={value}: no Elgato device")
        return False
    ok = False
    for path in found:
        auth = os.path.join(path, "authorized")
        try:
            with open(auth, "w", encoding="ascii") as f:
                f.write(str(value))
            print(f"USB authorized={value} {path}")
            ok = True
        except OSError as e:
            print(f"USB authorized={value} {path} failed ({e})")
    return ok


def reset_elgato_usb() -> bool:
    off = set_elgato_authorized("0")
    time.sleep(0.6)
    on = set_elgato_authorized("1")
    if off or on:
        time.sleep(USB_RESET_SETTLE_SECONDS)
        return True
    return False


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
    print(f"Self-restart ({reason})...")

    env = os.environ.copy()
    env["SUPERCRT_DECK_PAGE"] = CURRENT_PAGE
    env["SUPERCRT_DECK_ASLEEP"] = "1" if _asleep else "0"

    def _close() -> None:
        close_deck(deck)

    closer = threading.Thread(target=_close, name="deck-close", daemon=True)
    closer.start()
    closer.join(timeout=2.0)
    set_elgato_authorized("0")
    time.sleep(0.4)

    if os.environ.get("INVOCATION_ID"):
        print("Exiting for systemd restart")
        os._exit(0)

    reset_elgato_usb()
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


def set_key_image_from_url(deck, key: int, icon_url: str) -> None:
    try:
        response = requests.get(icon_url, timeout=4)
        if response.status_code != 200:
            print(f"Icon HTTP {response.status_code} for key {key}: {icon_url}")
            return
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        if hasattr(PILHelper, "create_scaled_key_image"):
            image_formatted = PILHelper.create_scaled_key_image(deck, image)
        elif hasattr(PILHelper, "create_key_image"):
            image_formatted = PILHelper.create_key_image(deck)
            image.thumbnail(image_formatted.size)
            image_formatted.paste(
                image,
                (
                    (image_formatted.width - image.width) // 2,
                    (image_formatted.height - image.height) // 2,
                ),
            )
        else:
            image_formatted = PILHelper.create_image(deck)
            image.thumbnail(image_formatted.size)
            image_formatted.paste(
                image,
                (
                    (image_formatted.width - image.width) // 2,
                    (image_formatted.height - image.height) // 2,
                ),
            )
        if hasattr(PILHelper, "to_native_key_format"):
            raw_bytes = PILHelper.to_native_key_format(deck, image_formatted)
        else:
            raw_bytes = PILHelper.to_native_format(deck, image_formatted)
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
    print(f"\nLoading page: {CURRENT_PAGE}")
    try:
        with deck:
            deck.set_brightness(WAKE_BRIGHTNESS)
    except Exception as e:
        print(f"reset/brightness: {e}")

    clear_all_keys(deck)
    page_data = PAGES.get(CURRENT_PAGE, {})
    for key, data in page_data.items():
        if "icon_url" in data:
            set_key_image_from_url(deck, key, data["icon_url"])
    print("Page rendered")


def go_to_sleep(deck) -> None:
    global _asleep
    with _lock:
        if _asleep:
            return
        print("Idle timeout — Stream Deck sleep")
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

    current_page_macros = PAGES.get(CURRENT_PAGE, {})
    if key not in current_page_macros:
        return

    button_data = current_page_macros[key]

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
    restore_state_from_env()
    beat()
    start_watchdog()

    print(f"Idle sleep after {IDLE_SLEEP_SECONDS}s ({IDLE_SLEEP_SECONDS // 60} min)")
    if PROCESS_REFRESH_SECONDS:
        print(f"Process refresh every {PROCESS_REFRESH_SECONDS}s ({PROCESS_REFRESH_SECONDS // 60} min)")
    print("Waiting for a USB Stream Deck (will retry if unplugged).")
    set_elgato_authorized("1")

    first_open = True
    open_fails = 0
    try:
        while True:
            deck = try_open_deck()
            if deck is None:
                open_fails += 1
                if open_fails in (1, 3, 8):
                    print("Open failed — USB reset")
                    reset_elgato_usb()
                time.sleep(RECONNECT_SECONDS)
                beat()
                continue
            open_fails = 0

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
                        print("Stream Deck disconnected — waiting to plug it back in.")
                        break
                    if not _asleep and (time.monotonic() - _last_activity) >= IDLE_SLEEP_SECONDS:
                        go_to_sleep(deck)
            except KeyboardInterrupt:
                print("\nStopping...")
                close_deck(deck)
                return
            except (TransportError, OSError) as e:
                print(f"Stream Deck USB error: {e}")
            finally:
                _active_deck = None
                if not _restarting:
                    close_deck(deck)
    except KeyboardInterrupt:
        print("\nStopping...")


if __name__ == "__main__":
    main()
