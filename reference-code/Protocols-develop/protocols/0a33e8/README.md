# PCR Prep Deep Well to 384

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 384 well plate with 5ul from (4) 96 deep well plates as the source. Deepwell plates should be placed in order of slot 4, 1, 5, 2 as sample number increases, with tips placed in order of slot 10, 7, 11, and 8. Samples in Plate 1 on slot 4 are completely transferred before moving onto Plate 2 on slot 1, so on and so forth. Plate 1 (slot 4) is dispensed into A1-A23 of the 384 plate, Plate 2 (slot 1) -> B1-B23 of the 384 plate, Plate 3 (slot 5) -> A2-A24 of the 384 plate, Plate 4 (slot 2) -> B2-B24 of the 384 plate. Negative and positive controls should be pre-loaded into O24 and P24 of the 384 well plate, and thus G12 and H12 of the Plate 4 on slot 2 should be empty.


Explanation of complex parameters below:
* `Number of Samples (1-382)`: Specify number of samples for this run. Negative and positive controls are always in O24 and P24 of the 384 plate, and so samples should not be placed in G12 and H12 of plate 4 on slot 2.
* `P20 Mount`: Specify which mount (left or right) to host the P20 multi-channel pipette.

---

### Labware
* Thermofisher 96 well plate
* Thermofisher 384 well plate

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/?_gl=1*1cts5dn*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY1ODg0MTkzMS4xMDA2LjEuMTY1ODg0NDkwNS4w)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0a33e8/Screen+Shot+2022-07-26+at+10.09.22+AM.png)

---

### Protocol Steps
1. Pick up tip
2. Add 5 uL of sample from the Deep Well to the microamp/PCR plate.
3. Drop Tip
4. Repeat for number of samples specified

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
0a33e8
