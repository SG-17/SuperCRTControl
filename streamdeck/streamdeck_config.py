from typing import Any

# Config — put your Super CRT-Control web server IP:PORT/IP/mDNS adddress below
# Example: http://192.168.1.251:8001 or http://192.168.1.251 or http://supercrt.local
SCC = "http://192.168.1.251"

# First page shown at startup
HOME_PAGE = "HOME"

# Stream Deck Orientation:
#   0   standard, top edge up,      5 columns × 3 rows
#   90  top edge faces right,       3 columns × 5 rows
#   180 upside down,                5 columns × 3 rows
#   270 top edge faces left,        3 columns × 5 rows
# Button number 0 is always in the top left position
ORIENTATION = 0

# Timers
IDLE_SLEEP_SECONDS = 1 * 60          # How long until the Deck sleeps, set to 60 seconds
WAKE_BRIGHTNESS = 40                 # How bright the Deck's buttons are, set between 0–100
PRESS_FLASH_SECONDS = 0.15           # White flash on key press. Set to 0 to disable
PROCESS_REFRESH_SECONDS = 60 * 60    # How often the program restarts itself, set to 60 minutes. Set to 0 to disable

# Pages: key index 0–14 (Stream Deck MK.2 = 15 keys)
# On each key you can have;
#   label, icon_url
#   url          — GET request to link
#   target_page  — switch to that page
#   You can have a url, a target page, or both

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
