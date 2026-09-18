from __future__ import annotations

import io
import threading
import time
from typing import Any

import requests
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Config: Put in your Super CRT-Control webserver IP:PORT below

SCC = "http://0.0.0.0:8001"

IDLE_SLEEP_SECONDS = 5 * 60          # 5 minutes
WAKE_BRIGHTNESS = 40                 # 0–100
POLL_SLEEP = 0.25

CURRENT_PAGE = "HOME"
_last_activity = time.monotonic()
_asleep = False
_lock = threading.Lock()

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
            "icon_url": f"{SCC}/images/deck/back.png",
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
            "icon_url": f"{SCC}/images/deck/back.png",
            "target_page": "HOME",
        },
        14: {
            "label": "Reset",
            "icon_url": f"{SCC}/images/deck/reset.png",
            "url": f"{SCC}/reset",
        },
    },
}

# Don't touch anything under this line

def touch_activity() -> None:
    global _last_activity
    _last_activity = time.monotonic()


def set_key_image_from_url(deck, key: int, icon_url: str) -> None:
    try:
        response = requests.get(icon_url, timeout=4)
        if response.status_code != 200:
            print(f"Icon HTTP {response.status_code} for key {key}: {icon_url}")
            return
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        if hasattr(PILHelper, "create_key_image"):
            image_formatted = PILHelper.create_key_image(deck, image)
        else:
            image_formatted = PILHelper.create_image(deck, image)
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
    print(f"\n Loading page: {CURRENT_PAGE}")
    try:
        with deck:
            deck.reset()
            deck.set_brightness(WAKE_BRIGHTNESS)
    except Exception as e:
        print(f"reset/brightness: {e}")

    page_data = PAGES.get(CURRENT_PAGE, {})
    for key, data in page_data.items():
        if "icon_url" in data:
            set_key_image_from_url(deck, key, data["icon_url"])
    print("Page loaded")


def go_to_sleep(deck) -> None:
    global _asleep
    with _lock:
        if _asleep:
            return
        print("Activity timeout — Keys sleeping")
        try:
            with deck:
                deck.set_brightness(0)
        except Exception as e:
            print(f"sleep brightness: {e}")
        clear_all_keys(deck)
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

    # First press while asleep only wakes
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


def main() -> None:
    streamdecks = DeviceManager().enumerate()
    if not streamdecks:
        print("No Stream Deck found over USB.")
        raise SystemExit(1)

    deck = streamdecks[0]
    deck.open()
    deck.set_brightness(WAKE_BRIGHTNESS)
    print(f"Opened: {deck.deck_type()} serial={deck.get_serial_number()}")
    print(f"Idle sleep after {IDLE_SLEEP_SECONDS}s ({IDLE_SLEEP_SECONDS // 60} min)")

    touch_activity()
    render_current_page(deck)
    deck.set_key_callback(button_callback)
    print("Super CRT-Control Stream Deck Remote active.")

    try:
        while True:
            time.sleep(POLL_SLEEP)
            if not _asleep and (time.monotonic() - _last_activity) >= IDLE_SLEEP_SECONDS:
                go_to_sleep(deck)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        try:
            with deck:
                deck.reset()
                deck.set_brightness(0)
            deck.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
