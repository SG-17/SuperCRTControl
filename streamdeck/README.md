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