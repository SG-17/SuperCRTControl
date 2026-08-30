# Super CRT-Control
A refined and upgraded take on Dochartaigh's [CRT-Control "Crosspoint RESPONSIVE Touchscreen-Control"](https://shmups.system11.org/viewtopic.php?t=69630) web app designed to be hosted on a dedicated local web server rather than the Extrons themselves. Allows for control of a virtually unlimited number of Extron Crosspoint Matrix Switchers with no limit on file sizes, page depth, or image quality. Crosspoints have a meager amount of file storage that one will quickly find themselves running up against if they have a large number of inputs and outputs in use. **Super CRT-Control** is designed to alleviate that. 
<img width="403" height="190" alt="20260829_185446" src="https://github.com/user-attachments/assets/197eb57e-717c-4292-8be0-c54855a0fa25" />
<img width="154" height="253" alt="20260821_191048" src="https://github.com/user-attachments/assets/1bdca065-2f53-4735-b73a-36bda6f1fc0d" />
<img width="148" height="242" alt="20260801_075523" src="https://github.com/user-attachments/assets/e7413a50-80bc-494c-b290-3c645737c92d" />

## Requirements
* Hardware to host a local web server
  * Windows PC
  * Linux PC
  * Raspberry Pi (even something as lightweight as the Zero W will work)
> [!TIP]
> If you intend for this device to run 24/7 a Linux-based device is a better choice than a Windows PC.
* Web server application of your choice
  * [nginx](https://github.com/nginx/nginx)
  * [python3](https://docs.python.org/3/library/http.server.html)
  * [SimpleWebServer](https://simplewebserver.org/)
  * [Apache](https://httpd.apache.org/)
  * [Windows IIS](https://www.iis.net/)
> [!NOTE]
> Since we are only serving web pages on your local network we do not need to worry about https, SSL, and so on.
> We just need to be able to serve .html pages and use javascript.
* A text editor that supports basic markdown is recommended but not required
  * [Notepad++](https://notepad-plus-plus.org/)
  * [Kate](https://kate-editor.org/)
  * [Nextpad++](https://nextpad.org/)
## Setup and Use
1. Download the latest release and extract to the folder that you assigned as the root of your web server.
2. 

