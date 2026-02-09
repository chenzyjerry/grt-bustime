# Instructions

So, you want to make your own GRT bus time display. If you do, bonus cool points! The instructions are as follows:

## Assemble Hardware

## Software Setup

### Install the OS

Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an OS on to your SD card. Select the device (Pi Zero 2W), and choose an OS. I used Raspberry Pi OS Lite (64-bit) Release 2025-12-04. Choose a hostname (i.e. pi-bustime) and follow the installation process to select your localisation, username/password, Wi-Fi network, and enable SSH.

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
mkdir bustime
cd bustime
```

Run the setup script. This will install all the required libraries:
```
bash setup.sh
```

Activate your virtual environment and run the script!
```
source venv/bin/activate
python bus_arrival_times.py
```

You should now be able to see a live status in your terminal on the next busses arriving at your stop. It will pull updated data every 3 minutes, and count down the arrival time in the meanwhile. Press ```Ctrl-C``` when you want to quit the program.

#### Debug

```bus_arrival_times.py``` has a debug mode to troubleshoot issues with data retrieval. This can be accessed by using the ```--debug``` flag:
```
python bus_arrival_times.py --debug
```