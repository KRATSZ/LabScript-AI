# Tube to Plate Viral Media Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
200ul of viral transport media (VTM) is reformatted from (up to) 96 tubes split amongst 3 tube racks to a  96 well plate. Tubes are reformatted by row in tube racks 1 (slot 1), 2 (slot 4), and then 3 (slot 7).

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for this run.
* `Tube Aspiration Height`: Specify the aspiration height in the tubes. Default is 1mm.
* `Well Dispense Height`: Specify the dispense height in the wells. Default is 1mm.
* `Aspirate/Dispense Flow rate`: Specify the aspirate/dispense flow rate in the wells. Default is 274ul/sec.
* `P1000 Single-Channel Mount`: Specify (left) or (right) mount for the P1000 single channel pipette.

---


### Labware
* [Opentrons 1000uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* Qiagen 96 Well plate
* (3) Custom Opentrons 32-tube tube racks.

### Pipettes
* [P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


---

### Deck Setup
* Deck layout with example 90 tubes. Note: tubes should be placed by row in the tube racks, starting from the tube rack in slot 1. Tubes are transferred 1-1 with well plate wells by row.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5829d7/Screen+Shot+2021-09-13+at+11.30.47+AM.png)

---

### Protocol Steps
1. Pick up tip
2. Aspirate 200ul of VTM
3. Dispense 200ul of VTM
4. Drop tip
5. 1-4 repeated by row in the tube racks.

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
5829d7
