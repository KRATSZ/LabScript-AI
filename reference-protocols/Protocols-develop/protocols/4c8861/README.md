# Normalization with Input .CSV File

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol normalizes up to (3) 96 well plates with diluent from 3 source plates to 3 destination plates. Destination plates exactly mirror source plates. The protocol begins by transferring diluent to all relevant wells in all 3 plates (up to 96 for each plate), and then continues to do a 1-1 well to well transfer between the source and destination plates. A csv is parsed to determine the transfer volume for each well of each plate.

Since the samples are temperature sensitive, the source plates are only loaded onto the deck one at a time, with the protocol pausing after all the diluent is added, and after each source plate is transferred. There is no mixing step in this protocol.



Explanation of complex parameters below:
* `CSV Sample`: Upload the csv sample with the following header line:
```
Plate number |	Well |	Concentration (ng/ul) |	Diluent Volume (ul) |	Sample volume (ul) |	Total volume (ul) |	Desired concentration(ng/ul)
```
* `Reset Tipracks`: Select `yes` to pick up the tip from A1 on the 200ul tip rack. Select `no` to pick up tip on the tip rack from where the previous run left off.
* `Include pauess`: Select `yes` to include pause steps after buffer is added and in between source plates that are completed. Select `no` otherwise. 
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 multi-channel pipette.
* `P300 Single-Channel Mount`: Specify which mount (left or right) to host the P300 single-channel pipette.

---

### Labware
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Opentrons 4-in-1 Tuberack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 20ul Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 200ul Tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4c8861/Screen+Shot+2021-10-07+at+3.20.33+PM.png)


---

### Protocol Steps
1. Transfer X(ul) of dilution buffer (slot 11) to output plate (slot 8) using single channel pipette (volume based on input concentration)
2. Pause after all 96 wells are filled, load input plate (slot 9)
3. Transfer Y(ul) input to left side of output plate (slot 8) wells and tip touch (to ensure total volume dispensed)
4. Pause, remove output (slot 8)
5 . transfer X(ul) of dilution buffer (slot 11) to output plate (slot 5) using single channel pipette (volume based on input concentration)
6. Pause after all 96 wells are filled, load input plate (slot 6)
7. Transfer Y(ul) input to left side of output plate (slot 5) wells and tip touch (to ensure total volume dispensed)
8. Pause, remove output (slot 5)
9. Transfer X(ul) of dilution buffer (slot 11) to output plate (slot 2) using single channel pipette (volume based on input concentration)
10. Pause after all 96 wells are filled, load input plate (slot 3)
11. Transfer Y(ul) input to left side of output plate (slot 2) wells and tip touch (to ensure total volume dispensed)
12. Pause, remove output (slot 2)


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4c8861
