# Parts List

If you want to make your own GRT Bus Arrival Time display, you will need the following parts:

## Raspberry Pi
| Name | Qty | Note |
| ---- | --- | ---- |
| Raspberry Pi Zero 2W (no headers) | 1 | You can buy the WH version if you don't want to solder the headers yourself. |
| 40 pin male header | 1 | To solder on to the Pi. Not needed if you bought the WH version. |
| MicroSD Card | 1 | I used a 64GB Lexar card, but you could definitely get away with significantly less. |

## Wiring HAT
| Name | Qty | Note |
| ---- | --- | ---- |
| 40 pin HAT female header | 1 | This makes your perfboard "Pi HAT" easy to install. |
| 5x7cm perfboard | 1 | Using a perfboard allows for your wiring to be very permanent and tidy without the fuss of a custom PCB. |
| 4 pin JST XH2.54 headers and cables | 2 | Headers are soldered to perfboard, cables to the 7-segment display modules. These allow you to replace modules without touching the HAT. |
| 3 pin JST XH2.54 headers and cables | 1 | Headers are soldered to perfboard, cables to the capacitive touch module. These allow you to replace modules without touching the HAT. |
| 24AWG wires (various colours) | N/A | For creating perfboard connections. |

## Components

| Name | Qty | Note |
| ---- | --- | ---- |
| TM1637 4-digit 7-segment display module (white) | 2 | The TM1637 is a convenient little I2C 7-segment display module that will eliminate the headache of having to manually control the 7-segment displays. White will allow the emitted light color to be altered using gel filters. |
| Orange gel filter sheet | 2 | This will make the display numbers orange just like the dot matrix displays in GRT bus shelters. |
| TTP223 Capacitive Touch Module | 1 | Capacitive touch module that allows the user to immediately refresh the arrival time data. Capacitive touch sensing allows the moduel to be hidden behind the front panel graphics. |

## Case

| Name | Qty | Note |
| ---- | --- | ---- |
