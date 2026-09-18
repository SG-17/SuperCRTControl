Linux Debian/Ubuntu Based

If using a microcomputer like a Raspberry Pi install Raspberry Pi OS full desktop for Pi 4 (2GB+) and Pi 5; Lite for Pi Zero 2 W, Pi 4 (1GB), and Pi 3). For OrangePi install Armbian, Desktop or Minimal depending on your hardware.

sudo apt update
sudo apt upgrade -y

sudo apt install -y python3 python3-pip python3-venv python3-pil
sudo apt install -y libusb-1.0-0-dev libudev-dev
sudo apt install -y libhidapi-libusb0 libhidapi-hidraw0
sudo apt install -y curl

echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", MODE="0666", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/10-streamdeck.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev "$USER"

lsusb | grep -i 0fd9

mkdir -p ~/supercrt/streamdeck
cd ~/supercrt/streamdeck
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install streamdeck requests pillow

sudo nano ~/supercrt/streamdeck/streamdeck.py
Update the IP and PORT on line 15 to match your Super CRT-Control web server install and configure your buttons starting on line 30.
If you are a masochist you can manually use nano for this in a terminal, but I'd recommend using a desktop environment in Linux or editing them on another machine and copying the files over (you can open an ssh via PuTTY or something on another machine and quickly copy the contents over in nano too).

cd ~/supercrt/streamdeck
source venv/bin/activate
python3 streamdeck.py



sudo nano /etc/systemd/system/streamdeck.service


[Unit]
Description=Super CRT Stream Deck Remote
After=network-online.target

[Service]
Type=simple
User={YOURUSERNAME}
Group={YOURUSERNAME}
WorkingDirectory=/home/{YOURUSERNAME}/supercrt/streamdeck
ExecStart=/home/{YOURUSERNAME}supercrt/streamdeck/venv/bin/python /home/{YOURUSERNAME}/supercrt/streamdeck/streamdeck.py
Restart=on-failure
RestartSec=20

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable --now streamdeck
sudo systemctl status streamdeck


sudo systemctl restart streamdeck


Windows 10/11

Install the official Stream Deck software.
Use the Website key under System.
Place the alias url you want in "URL:".
Set the dropdown to "GET request in background".
Change the icon to what you want.
