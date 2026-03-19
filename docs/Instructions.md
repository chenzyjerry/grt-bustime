# Instructions

So, you want to make your own GRT bus time display. If you do, bonus cool points! The instructions are as follows:

## Assemble Hardware

1. Cut your 7x9cm perfboard lengthwise so you are left with a roughly 2x9cm segment.

2. Solder 40 pin male header onto Raspberry Pi Zero 2W.

2. Solder 40 pin female header onto perfboard.

3. Solder two 4-pin right-angle JST-XH and one 3-pin right-angle JST-XH header onto the perboard. Solder the corresponding 4 pin cables to the display modules, and the 3 pin cable to the touch sensor. I would also recommend adding hot glue to the solder joints for strain relief.

4. Connect the Pi headers to the JST-XH headers on the perfboard as per the following diagram: ![Wiring Diagram](./img/GRT_Bustime%20Wiring%20Diagram.png)

5. Plug the display and touch modules into the perfboard hat, and the hat into the Pi. It should look similar to the following: ![Assembled Components](./img/ComponentsLaidOut.png)

6. You should now be done the electrical components. You can choose to test all the components prior to assembly in the case. For that, skip to the Software Setup section.

## Make the Case

All required files can be found in the ```print_files``` folder.

1. 3D print the Bottom Case, Top Case, PCB Support Bracket, and Pi Frame. If you'd like to make it desk mounted, also print out 2 of the Legs.

2. Laser cut the acrylic sheet as per ```Acrylic Faceplate.DWG```.

3. Print out ```GRT Bus Time Face Decal.pdf```. Ensure that it prints to the proper scale. Cut out the black boxes for the displays, and use the acrylic faceplate as a guide to cut out the corners and punch the screw holes. Place a small square of transparent tape over the refresh button location.

4. Add the two 6mm M2.5 heat inserts to the PCB support bracket.

5. Add the four M3 heat inserts to the corners of the Bottom Case. Add the 4mm M2.5 heat inserts to XYZ, and the 6mm M2.5 heat inserts to ABC.

6. Add four M3 heat inserts to each corner of the display brackets on the inside face of the Top Case.

> [!NOTE]
> If you want to make it desk mounted, slot the M3 nuts into the hexagonal holes on the Bottom Case. Fasten the legs to the case using the four M3xX screws from the back of the case.

7. Plug the MicroUSB power supply into the Pi.

> [!WARNING]
> The power supply must be plugged in prior to assembly, as it is not possible to do so once the case is closed.

7. Secure the Pi to the Bottom Case using the four M2.5xX screws, with the Pi Frame underneath as a spacer.

8. Secure the perfboard to the PCB Support Bracket using the two M2.5xX screws. Plug the perfboard into the Pi. Secure the PCB Support Brackets to the Bottom Case using the two MXxX screws.

9. Secure the touch sensor to the slot in the top case with electrical tape.

10. Plug in the display modules and touch sensor prior to closing the case. It should now look like the following: ![Components Installed](./img/ComponentsInstalled.png)

11. Place the Top Case on the Bottom Case. Place the Face Decal on top, and then the acrylic faceplate on top of that. Secure the entire assembly using the four M3xX screws and washers.

## Software Setup

### Install the OS

Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an OS on to your SD card. Select the device (Pi Zero 2W), and choose an OS. I used ```Raspberry Pi OS Lite (64-bit) Release 2025-12-04```. Choose a hostname (i.e. pi-bustime) and follow the installation process to select your localisation, username/password, Wi-Fi network, and enable SSH.

### Connect to the Pi

Use SSH to connect to your Pi. You can do this many ways, such as directly through your terminal, or using clients like [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/) or my preferred client, [Tabby](https://github.com/Eugeny/tabby). Log in using the username and password you used when installing the OS.

### Download the code

Update your package list and install Git:
```
sudo apt update
sudo apt install git -y
```

Make a folder where you want the GRT-Bustime code to live and navigate to it:
```
mkdir grt-bustime
cd grt-bustime
```

Clone the repo:
```
git clone https://github.com/chenzyjerry/grt-bustime.git
```

Run the setup script. This will install all the required libraries:
```
cd src
bash setup.sh
```

### Edit the configuration file

There is a configuration text file which will allow you to set things like display brightness, stop number, route numbers, etc. More information on these settings can be found in ```Configuration.md```. Navigate to the file using 
```
nano config.txt
```

Edit the configuration, and then save your changes with ```Ctrl-O, Enter, Ctrl-X```.

### Run the code

Activate your virtual environment and run the script!
```
source venv/bin/activate
python bus_arrival_times.py
```

You should now be able to see a live status in your terminal on the next busses arriving at your stop. It will pull updated data every 3 minutes. Press ```Ctrl-C``` when you want to quit the program.

### Run on Startup with Crontab

To automatically run the script when your Raspberry Pi starts, you can use crontab:

1. Make the startup script executable:
```
chmod +x ~/grt-bustime/src/run_bustime.sh
```

2. Open the crontab editor:
```
crontab -e
```

3. Add this line to the end of the file:
```
@reboot /home/YOUR_USERNAME/grt-bustime/src/run_bustime.sh
```

Replace `YOUR_USERNAME` with your actual Raspberry Pi username.

4. Save and exit (press `Ctrl-O`, then `Enter`, then `Ctrl-X`)

5. Verify the entry was added:
```
crontab -l
```

The script will now automatically start when your Pi boots up. Output is logged to `~/grt-bustime/src/bustime.log`, which you can check to troubleshoot any issues:
```
cat ~/grt-bustime/src/bustime.log
```
