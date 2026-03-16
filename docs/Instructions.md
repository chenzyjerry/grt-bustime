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

To keep the program running in the background even after you disconnect from SSH, you can use [tmux](https://github.com/tmux/tmux), which allows you to run a detached terminal in the background. Install tmux:
