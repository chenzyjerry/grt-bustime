What: GRT bus arrival time display for the next 19 and 12 busses at my closest bus stop (2783). Display will allow me to decide when to leave to catch a bus to class.

Hardware:
- Raspberry Pi Zero V2: Fetches bus arrival times every 3 minutes from [GRT API](https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates) and displays arrival times in (MM:SS) format on two 7-segment displays.
- Two 7-segment displays: Displays next bus arrival times.
- Capacitive button: Allows user to force refresh arrival time.

Software Design:
- Bus Stop # (2783) and the two bus route numbers (12, 19) stored in plain text in .csv format to allow easy editing without having to touch the code
- Fetch and display time:
	- Fetch bus arrival times every 3 minutes from [GRT API](https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates), as a file in protobuf format
		- If fetching fails, display *FEt Err* on the displays (*FEt* on one display, *Err* on the second)
	- Parse protobuf file, which stores data in the [GTFS](https://gtfs.org/) format, for stop 2783, and record the next arrival times for the 19 and 12 busses.
	- Display this time to each of the 7-segment displays
	- Edge case handling:
		- If next bus is cancelled/my stop will be skipped, display time for the bus after.
		- If next bus is over 1hr away (aka, nighttime service end), display *----*.
- Use interrupts to monitor for capacitive button presses to force fetch and display process

Mechanical Design:
- Pi has a custom perfboard HAT which simplifies all the wiring.
- Pi is mounted near to bottom of case (using standoffs), allowing for power supply to be directly plugged in.
- Front panel is 3 layers: Base layer is a 3D print to which components are mounted, middle layer is a printed graphic, outer layer is a clear piece of acrylic.
	- 7-segment display and capacitive button are mounted to front panel base layer and connected to HAT via removable JST headers/connectors. This will allow for modules to be easily replaced without having to mess with the soldering on the perfboard.
		- White 7-segment displays have orange gel filter to resemble the official dot-matrix orange signage
	- Middle graphic layer is themed to make it look like official GRT bus stop signage.
		- This sandwich design allows for the graphic layer to be exchanged in case I move and a different stop is nearby, or I move cities and the transit agency changes. I would only need to reprint a piece of paper, which I can do even if I live somewhere without access to a 3D printer/other tools.
		- Blue, white, and gold graphics in Arial Bold or whatever the official font is.
		- Bus route number (12, 19) printed next to each display.
		- Small circled 👆 icon over the capacitive button.
	- Outer acrylic layer sandwiches all layers and screws into case
- Case is rectangular with rounded edges similar to the bus stop signs. Sanded smooth and spray painted silver to imitate official metal signage
- Mounted to wall using 3M 5lb adhesive strip