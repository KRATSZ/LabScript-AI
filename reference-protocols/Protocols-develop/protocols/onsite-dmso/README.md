# Diluting Samples with DMSO

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

Explanation of complex parameters below:
* `csv`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line, with volume in the 6th column:
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-dmso/Screen+Shot+2022-06-27+at+4.46.37+PM.png)
* `Tubes on Slot 4`: Specify which tube rack to use on slot 4. 
* `P1000 Mount`: Specify which mount (left or right) to host the P1000 single channel pipette

---


### Labware
* Custom Opentrons 4-in-1 tube rack
* Altemis lab 48 plate
* Micronic 96 well plate
* Nest 1-well Reservoir

### Pipettes
* [P1000 Single-Channel pipette]()

### Reagents
* DMSO

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-dmso/Screen+Shot+2022-06-27+at+4.51.24+PM.png)

---

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
onsite-dmso
