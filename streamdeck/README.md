## Linux Debian/Ubuntu Based

If using a microcomputer like a Raspberry Pi install Raspberry Pi OS full desktop for Pi 4 (2GB+) and Pi 5; Lite for Pi Zero 2 W, Pi 4 (1GB), and Pi 3).  
For OrangePi install [Armbian](https://armbian.com/boards/orangepizero2w), Desktop or Minimal depending on your hardware.

First plug your Stream Deck into your Linux machine.  
Open a terminal/connect via ssh.  
Run the basic update.
```
sudo apt update
sudo apt upgrade -y
```

Next install python3 and the USB interface libraries for the Stream Deck.
```
sudo apt install -y python3 python3-pip python3-venv python3-pil
sudo apt install -y libusb-1.0-0-dev libudev-dev
sudo apt install -y libhidapi-libusb0 libhidapi-hidraw0
sudo apt install -y curl
```

Update the udev rules to allow the Stream Deck to be usable by all users.
```
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", MODE="0666", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/10-streamdeck.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo usermod -aG plugdev "$USER"
```

Unplug the Stream Deck and then plug it back in. Run the below to check that it is now properly being seen.
```
lsusb | grep -i 0fd9
```

Create the python environment that the Stream Deck controller program will run in. If you followed the instructions for the installation of Super CRT-Control then the `~/supercrt/streamdeck` directory should already exist.
```
mkdir -p ~/supercrt/streamdeck
cd ~/supercrt/streamdeck
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install streamdeck requests pillow
```

Update the IP and PORT on line 15 to match your Super CRT-Control web server install and configure your buttons starting on line 30 using the alias URLs you set up during the main Super CRT-Control install.  
If you are a masochist you can manually use nano for this in a terminal, but I'd recommend using a desktop environment in Linux or editing them on another machine and copying the files over (you can open an ssh via PuTTY or something on another machine and quickly copy the contents over in nano too).
```
sudo nano ~/supercrt/streamdeck/streamdeck.py
```

Enter the python environment and test that the program runs correctly. Ctrl+C to shut it down while its running in terminal.
```
cd ~/supercrt/streamdeck
source venv/bin/activate
python3 streamdeck.py
```

Create the service to run the Stream Deck controller program in the background and on system boot.
```
sudo nano /etc/systemd/system/streamdeck.service
```

Change `{YOURUSERNAME}` to, you guessed it, your username on Linux. On a basic Raspberry Pi OS install this might just be `pi`.  
Copy and paste the edited version into the opened `streamdeck.service` file, Ctrl+X and then press Y to save.
```
[Unit]
Description=Super CRT Stream Deck Remote
After=network-online.target

[Service]
Type=simple
User={YOURUSERNAME}
Group={YOURUSERNAME}
WorkingDirectory=/home/{YOURUSERNAME}/supercrt/streamdeck
ExecStart=/home/{YOURUSERNAME}/supercrt/streamdeck/venv/bin/python /home/{YOURUSERNAME}/supercrt/streamdeck/streamdeck.py
Restart=always
RestartSec=20

[Install]
WantedBy=multi-user.target
```

Reload the system service daemon, enable the Stream Deck Controller program, and check its status to see if its running correctly.
```
sudo systemctl daemon-reload
sudo systemctl enable --now streamdeck
sudo systemctl status streamdeck
```

If you need to make changes to `streamdeck.py` you'll need to run the below to apply them.
```
sudo systemctl restart streamdeck
```
Now if everything is running correctly your Stream Deck should now be populated with the buttons you created in the `streamdeck.py` file.  

## Windows 10/11
Considering that the official Stream Deck software supports background GET requests and folders I don't see the point is creating a custom program for Windows. 

* Install the [official Stream Deck software](https://www.elgato.com/us/en/s/stream-deck-app).
* Use the Website key under System.
* Place the alias url you want in "URL:".
* Set the dropdown to "GET request in background".
* Change the icon to what you want.
