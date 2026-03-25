# Custom Tuberack Dilutions

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Dilution

## Description

This protocol performs a dilution on custom tuberacks with 2x P1000 pipettes in tandem. The deck layout is shown below:  
![deck3d](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5eee17/deck3d.png)

---

### Labware
* Custom 15ml, 50ml, and HPLC tuberacks
* [Opentrons 1000µL Tips](https://shop.opentrons.com/opentrons-1000-l-tips/)

### Pipettes
* [2x Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5eee17/deck2d.png)

---

### Protocol Steps
1. Both pipettes pick up 1000µL tip
2. Pipette 1 aspirates 700µL from tube at position 1 on rack 1 with air gap
3. Pipette 2 aspirates 700µL from tube at position 2 on rack 1 with air gap
4. Pipette 1 dispenses full volume into tube at position 1 on rack 3
5. Pipette 1 mixes using 1000µL volume 5x
6. Pipette 1 aspirates 800 µL from mixed dilution tube
7. Pipette 1 dispenses full volume into vial at position 1 on HPLC rack at deck position 11
8. Pipette 2 dispenses full volume into tube at position 2 on rack 3
9. Pipette 2 mixes using 1000µL volume 5x
10. Pipette 2 aspirates 800 µL from mixed dilution tube
11. Pipette 2 dispenses full volume into vial at position 2 on HPLC rack at deck position 11
12. Pipette 1&2 discard tips in waste tray
13. Steps 1-12 are repeated for as many samples as specified, pausing for refills if more than 48 samples are input.


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
5eee17
