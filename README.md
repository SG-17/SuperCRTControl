# Super CRT-Control
A refined and upgraded take on Dochartaigh's [CRT-Control "Crosspoint RESPONSIVE Touchscreen-Control"](https://shmups.system11.org/viewtopic.php?t=69630) web app designed to be hosted on a dedicated local web server rather than the Extrons themselves. Allows for control of a virtually unlimited number of Extron Crosspoint Matrix Switchers with no limit on file sizes, page depth, or image quality on any web capable device on your local network such as an old tablet or your phone. Crosspoints have a meager amount of file storage that one will quickly find themselves running up against if they have a large number of inputs and outputs in use. **Super CRT-Control** is designed to alleviate that.  

**Super CRT-Control** can be used in combination with the [DonutDongle](https://github.com/svirant/DonutDongle) and a next gen RetroTink (6X CE, 4K CE, 4K Pro) to auto-load profiles on the RetroTink.

|  |  |  |  |  |
|     :---:      |     :---:      |     :---:      |     :---:      |     :---:      |
| [Requirements](#Requirements)   | [Extron Setup](#setting-up-your-extron)  |  [Super CRT-Control Setup Guide](#setup-and-use-of-super-crt-control)  | [Project Status and Disclaimers](#Project-Status-and-Disclaimers) |[Special Thanks](#Special-thanks) |

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
> Since we are only serving web pages on your local network we do not need to worry about https/ssl/etc.
> We just need to be able to serve .html pages and use javascript.
* A text editor that supports basic markdown is recommended but not required
  * [Notepad++](https://notepad-plus-plus.org/)
  * [Kate](https://kate-editor.org/)
  * [Nextpad++](https://nextpad.org/)
    
* A supported Extron Matrix Switcher
  * Extron Crosspoint MAV Plus, 450 Plus, Ultra
  * Extron DXP DVI, DXP HDMI, HD 4K, HD 4K Plus
  * Extron MVX VGA
  * Potentially other Extrons and other brands; a switch that can load presets via a web app will likely work if the command format can be discovered.
    
* Your Extron wired to your local network via ethernet and setup with a [static IP](https://github.com/SG-17/SuperCRTControl/tree/main#ip-address-setup).
  * You can find instructions by searching for your Extron device and reading the user manual, for example [this](https://media.extron.com/public/download/files/userman/68-521-50_C.pdf) is the manual for the 450 and Ultra.
  * You may need a [DB9/RS232 to USB cable](https://www.amazon.com/Adapter-Prolific-Chipset-CableCreation-Converter/dp/B0758BWVXF) and the Extron Matrix Switcher Control Program to set a static IP, you can find the program via the Internet Archive.
    
* [Presets](https://github.com/SG-17/SuperCRTControl/tree/main#saving-presets) setup on your Matrix
  * You can set presets via the front buttons, via the ***Extron Matrix Switcher Control Program***, or via the Matrix's native web control which can be accessed at the static IP you set.

## Setting up your Extron

### Front Panel Reset
When you first receive your Extron it is good practice to perform a front panel reset.  
To do this press and hold the Video and Audio buttons <img width="54" height="40" alt="image" src="https://github.com/user-attachments/assets/f740a199-a63d-4ce1-94f0-d978c12e2c26" /> simultaneously while plugging the Extron into power.  
The buttons will flash and turn off, keep holding until they turn back on. This removes any preexisting presets or settings that may interfere with your use.  

### IP Address Setup
In order to use your Extron with Super CRT-Control it will need to be connected to your local network and setup with a static IP address.  
There are several ways to do this. Plug your Extron into an ethernet cable and into your home network to get started. Using a powerline or wireless bridge should work fine.  

1. Via the existing IP Address
   - By default all Extrons will have the ip `192.168.254.254` assigned to them. If the previous owner did not change this you *should* be able to enter it in a web browser and access settings from there.
   - Open the Default Web Page and click on **Configuration**.
     <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/4f1da827-fc6e-407e-9bba-617c4aca104c" />
   - Under `IP Settings` turn **DHCP** to **Off**.
   - Enter the **IP Address** you want to assign the Extron along with the **Gateway Address** and **Subnet Mask** that matches your network. Click **Submit**.
     <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/151dc331-99d4-42d7-ab01-219f00771b55" />
     
2. Via the Extron Matrix Switcher Control Program over a Serial RS-232 connection
   - Connect a [DB9/RS232 to USB cable](https://www.amazon.com/Adapter-Prolific-Chipset-CableCreation-Converter/dp/B0758BWVXF) to the DB9 port on the rear of the Extron <img width="36" height="44" alt="image" src="https://github.com/user-attachments/assets/c5acca52-1e77-4f42-abb7-a94fe732ad96" />. Connect the other end to a ***rear USB port*** on your Windows PC.  
     Or  
   - Connect a [USB RS232 to 3.5mm cable](https://www.amazon.com/dp/B07XXWVH69) to the **Config** port on the front of your Extron if present. Connect the other end to a ***rear USB port*** on your Windows PC.
   - Download and install the [Extron Matrix Switcher Control Program](https://archive.org/details/matrix-sw-v-8x-4).
   - Open your **Device Manager** in Windows and look under `Ports (COM & LPT)` to find out which COM number your Extron is on.
   - Launch the Extron Matrix Switcher Control Program.
     - Click the button for the COM port you found above or click **More** and enter the number and click **OK**
       <img width="150" height="195" alt="image" src="https://github.com/user-attachments/assets/beeb0dfa-3d38-4288-8e5a-3081b1e4075b" />
	 - Click **Tools --> IP Options**.
       <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/25f9601f-0c29-463c-9fb5-0b5829964cbd" />
	 - Uncheck `Use DHCP` and enter **IP Address** you want to assign the Extron along with the **Gateway Address** and **Subnet Mask** that matches your network. Click **Take**.
       <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/b0fabdb2-fd64-4256-b447-0e92cd8d5522" />
	 - Click the **X** in the upper right corner of the program to close it, when it asks to save select **Yes**.
       <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/4d7d6dc7-e690-42d6-9639-ff19527dc3c1" />

### Saving Presets
Now that you have your Extron on your network we can begin creating the presets that Super CRT-Control will load for you.  
There are several ways to do this but the simplest is by using the **Default Web Page** so that is the only method I will enumerate. 

1. Press the **ESC** button on the front of your Extron to clear any selections.
   
2. Enter the IP you assigned your Extron into your web browser and click **Control**.
   
3. On the **Set and View Ties** page that opens make sure that `Video & Audio` is selected.
   
4. In the grid below you have the **Inputs** on the rows and the **Outputs** on the columns
   - Find the row that matches the input you want to use and then click the box in the column of the output you want to use.
     - You can assign an input to as many outputs as you want and you can have multiple inputs going to different outputs at the same time.
       - Outputs ***cannot*** overlap.  
   - Once you have the configuration you want click **Take**.  
     <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/a5b42dc6-e8d4-4cb4-bb5f-90165c8c0d79" />
     
5. Now that you have an input/output configuration that you want to save as a preset active click on **Global Presets** on the left-hand menu.
   - On the **Global Presets** page click on **Save Preset** to activate the selector.
   - Click on the `[unassigned]` button you want for your preset.
   - If desired enter a name in the text box next to the **Select Preset..** button.
   - Click **Accept** to save the preset. The number next to the preset you saved will be used when setting up Super CRT-Control.
     <img width="565" height="404" alt="image" src="https://github.com/user-attachments/assets/b2537f9e-9372-4404-8018-2728e185dde3" />
     
6. Repeat steps 2 - 5 to create as many presets as you'd like.

## Setup and Use of Super CRT-Control
1. Download the latest [release](https://github.com/SG-17/SuperCRTControl/releases) and extract to the folder that you assigned as the root of your web server.

2. Decide which size button layout will be your home page.
   If you are using a size other than 16 delete or rename the `index.html` in the .zip, make a copy of the .html file that matches the size you want(such as `control12.html`), rename it to `index.html`, and open it in your text editor of choice.

3. Set your command links by entering the static IP Address(es) of your Extron Matrix Switcher(s) that you use to access the web control menu, followed by `?cmd=#.`.   
 	* Replace the `#` with the number of the preset on the Extron that the link will be loading. The period (`.`) at the end is necessary, do not delete it.

4. Check the `images` folder to make sure that all of the buttons you want to use are present.
   If you need something that isn't present use the [Touchscreen Button.psd](https://github.com/SG-17/SuperCRTControl/blob/main/Utilities/Buttons/Extra%20Templates/Touchscreen%20Button.psd) template to create it.

5. Change the image link to the matching image you desire and the alt text to match.
   Example below:  
	* `<a href="http://192.168.1.252/?cmd=1." target="iframe"><img src="images/psx-crt-c.png" alt="PS1" type="button"></a>`

6. You can link to submenus or second pages for more systems or game specific presets by simply linking to the new page.
   Example below:  
	* `<a href="/controlps2.html"><img src="images/ps2-crt-c.png" alt="PS2 Submenu" type="button"></a>`  
	* Be sure that `target="iframe"` is ***not*** included in submenu links.  
	* If your main page is named `index.html` a simple `/` in the `href=` of a link on a submenu page will take you back to the main page.

7. Set the style link on line 7 in the header to match the number of buttons you will use for a subpage.
   Examples below:
    ```
	<link href="/css/style12.css" rel="stylesheet">
	<link href="/css/style16.css" rel="stylesheet">
	<link href="/css/style20.css" rel="stylesheet">
	<link href="/css/style32.css" rel="stylesheet">
	```  
    
8. If you need a button to load a preset on more than one Extron at a time use the following format for the link:  
	```
 	<a href="#" onclick="multiCmd([
 		'http://192.168.1.249/?cmd=5.',
		'http://192.168.1.252/?cmd=7.'
		]); return false;">
			<img src="images/gamecube-crt-c.png" alt="NGC (both)" type="button">
	</a>
	```
  
9. Once you have configured your html code you can start using your Super CRT-Control to control your Extron Matrix Switchers.

## Project Status and Disclaimers
> This project comes with no guarantees or timetables.
> 
> This project is tailored to enthusiasts who either have the skills or the drive to learn the skills to implement it.  
> Support will not be provided for setting up a local web server.
> 
> All testing has been done on a Samsung Galaxy Tab 3 7.0 using an old version of Firefox Android, a newer Samsung Galaxy phone using a current version of Firefox Android, and a Windows 10 PC and Linux Mint PC both using current versions of Firefox.

## Special Thanks
A special thanks to [Dochartaigh](https://shmups.system11.org/memberlist.php?mode=viewprofile&u=17494) who created the original [CRT-Control](https://shmups.system11.org/viewtopic.php?t=69630).  
[donutswdad](https://github.com/svirant) for creating the [DonutDongle](https://github.com/svirant/DonutDongle) and for helping me troubleshoot some issues I was having with my DXP HDMI.  
[ihategravel](https://github.com/ihategravel2) for creating [several](https://github.com/ihategravel2/RCA-Phoenix) [cool](https://github.com/ihategravel2/10Pin-Phoenix-Audio-Adapter) Extron add-ons.
