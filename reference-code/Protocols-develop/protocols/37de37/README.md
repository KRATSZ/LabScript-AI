# Cherrypicking DNA and Pooling with CSV input

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Cherrypicking

## Description
This protocol normalizes DNA transfers with diluent via a user imported .csv. Diluent is transferred to all relevent wells, and then DNA is premixed (from up to 3 source plates) and added to the diluent well, post-mixed, and pooled in H12 of the final plate.

Explanation of complex parameters below:
* `.CSV File`: : Here, you should upload a .csv file formatted in the following way, being sure to include the header line:
```
Sample number,Plate number, Source well, Destination well, Start Concentration (ug/uL) Source, Final Concentration (ug/ml) Destination, Sample volume (uL), Diluent Volume(ul), Total Volume(ul) Destination
```
NOTE: Plate number in the .csv file (column 2) should be either 1, 2, or 3, since the protocol can handle up to 3 source plates.
* `Number of Source Plates`: Specify the number of source plate in this protocol.
* `P20 Single-Channel Mount`: Specify which mount (left or right) to mount the Opentrons P20 Single Channel pipette.


---

### Labware
* [Corning 384 Well Plate 360 µL](https://www.corning.com/catalog/cls/documents/drawings/DWG00834.PDF)
* [Brooks Life Sciences 21mL 15-well reservoir](https://www.brookslifesciences.com/products/reservoir-plate)
* [Opentrons 20uL Tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P20 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/37de37/Screen+Shot+2021-09-23+at+4.38.30+PM.png)

---

### Protocol Steps
1. Transfer volume of diluent as per CSV (1 tip only needed) up to 3 source plates
2. Mix DNA and transfer from initial to the final plate (as per CSV), then mix after dispensing.
3. Pool 5ul of each sample into H12 of the final plate.

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
37de37
