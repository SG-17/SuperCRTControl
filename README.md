# Super CRT-Control
A refined and upgraded take on Dochartaigh's [CRT-Control "Crosspoint RESPONSIVE Touchscreen-Control"](https://shmups.system11.org/viewtopic.php?t=69630) web app designed to be hosted on a dedicated local web server rather than the Extrons themselves. Allows for control of a virtually unlimited number of Extron Crosspoint Matrix Switchers with no limit on file sizes, page depth, or image quality. Crosspoints have a meager amount of file storage that one will quickly find themselves running up against if they have a large number of inputs and outputs in use. **Super CRT-Control** is designed to alleviate that. 
<img width="403" height="190" alt="20260829_185446" src="https://github.com/user-attachments/assets/197eb57e-717c-4292-8be0-c54855a0fa25" />
<img width="148" height="242" alt="20260801_075523" src="https://github.com/user-attachments/assets/e7413a50-80bc-494c-b290-3c645737c92d" />
<img width="154" height="253" alt="20260821_191048" src="https://github.com/user-attachments/assets/1bdca065-2f53-4735-b73a-36bda6f1fc0d" />


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
* A supported Extron Matrix Switcher
  * Extron Crosspoint MAV Plus, 450 Plus, Ultra
  * Extron DXP DVI, DXP HDMI, HD 4K, HD 4K Plus
  * Extron MVX VGA
* Your Extron wired to your local network via ethernet and setup with a static IP
  * You can find instructions by searching for your Extron device and reading the user manual, for example [this](https://media.extron.com/public/download/files/userman/68-521-50_C.pdf) is the manual for the 450 and Ultra.
  * You may need a [DB9/RS232 to USB cable](https://www.amazon.com/Adapter-Prolific-Chipset-CableCreation-Converter/dp/B0758BWVXF) and the Extron Matrix Switcher + Control Program to set a static IP, you can find the program via the Internet Archive.
* Profiles setup on your Matrix
  * You can set profiles via the front buttons, via the Extron Matrix Switcher + Control Program, or via the Matrix's native web control which can be accessed at the static IP you set.
## Setup and Use
* Download the latest release and extract to the folder that you assigned as the root of your web server.

* Decide which size button layout will be your home page, copy and paste that .html file (such as `control12.html`) and rename it to `index.html` and open it in your text editor of choice.

* To set a command link enter the static IP Address of your Extron Matrix Switcher that you use to access the web control menu followed by `?cmd=#.`.   
  * Replace the `#` with the number of the profile on the Extron that the link will be loading. The period (.) at the end is necessary, do not delete it.  

* Change the image link to the matching image you desire and the alt text to match.  
  * Example below:  
	* `<a href="http://192.168.1.252/?cmd=1." target="iframe"><img src="images/psx-crt-c.png" alt="PS2" type="button"></a>`  
    
* You can link to submenus or second pages for more systems or game specific profiles by simply linking to the new page.  
  * Example below:  
	* `<a href="/controlps2.html"><img src="images/ps2-crt-c.png" alt="PS2 Submenu" type="button"></a>`  
	* Be sure that 'target="iframe"' is not included in submenu links.  
	* If your main page is named `index.html` a simple `/` in the `href=` of a link on a submenu page will take you back to the main page.  

* Set the style link on line 7 in the header to match the number of buttons you will use for a subpage.  
  * Examples below:  
	* `<link href="/css/style12.css" rel="stylesheet">`
	* `<link href="/css/style16.css" rel="stylesheet">`
	* `<link href="/css/style20.css" rel="stylesheet">`
	* `<link href="/css/style32.css" rel="stylesheet">`  

* If you need a button to load a profile on more than one Extron at a time use the following format for the link:  
	```
 	<a href="#" onclick="multiCmd([
 		'http://192.168.1.249/?cmd=5.',
		'http://192.168.1.252/?cmd=7.'
		]); return false;">
			<img src="images/gamecube-crt-c.png" alt="NGC (both)" type="button">
	</a>
	```
       
* Once you have configured your html code you can start using your Super CRT-Control to control your Extron Matrix Switchers.

