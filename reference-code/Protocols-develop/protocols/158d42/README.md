# PCR Prep with Custom 32 Tuberacks

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description

This protocol preps a 96 well PCR plate with up to 46 samples. The order of operations is: transfer negative control to A1 of the well plate, transfer samples down plate columns starting from C1, transfer positive control to A12 of well plate, then B1. Resuspension steps are included after most transfers. For wells with powdered reagent, roughly half of the necessary volume is dispensed into the well from half of the well depth, then the pipette tip proceeds to travel to the bottom of the well to dispense the rest of the required volume and mix. Sample in buffer is transferred from the 32-tube rack to the 24 tube rack which contains sterile normalization buffer, and the resulting mixture is then added to the plate.

Explanation of complex parameters below:
* `Number of tubes (1-46)`: Specify the number of tubes placed in the custom 32-tube tube racks. Tubes should be placed by row, and up down (from slot 7 to slot 4).
* `Use Temperature Module`: Specify whether or not to use the temperature module at 12C this run. If not, you can place the plate directly on slot 1.
* `P300 Mount`: Specify which mount (left or right) to host the P300 single-channel pipette.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Opentrons 4-in-1 24 tube tube rack with 1.5mL tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 100ul PCR Plate, Full Skirt](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [Opentrons 200ul Filter tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* Custom 32 tube tube racklink to labware on shop.opentrons.com when applicable


### Pipettes
* [P300 Single-Channel Pipette](https://shop.opentrons.com/pipettes/)

---

### Deck Setup
* 24 tube racks should be placed in order of slots 9, 6. Tubes by row.
* 32 tube racks should be placed in order of slots 7 and 4. Tubes by row.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1584d2/Screen+Shot+2022-06-09+at+10.34.00+AM.png)

---

### Protocol Steps
1. Preparation of negative control: Transfer 50 μl of sterile Control Buffer (1.5 ml tube) to the first PCR tube in an 8-well strip containing lyophilized PCR mix, resuspend.
2. Preparation of unknown samples: Transfer 50 μl of the unknown sample in SAVD buffer (5 ml tube) to 250 μl sterile Normalization buffer (1.5 ml tube). Resuspend.
3. Transfer 50 μl of the normalized unknown sample to the next PCR tube in the 8-well strip containing lyophilized PCR mix. Resuspend. Repeat for each unknown sample.
4. Preparation of positive control: Transfer 50 μl of sterile Normalization Buffer (1.5 ml tube) to the Positive Control Tube (lyophilized in PCR tube). Resuspend.
5. Transfer 50 μl of the positive control mixture to the H12, resuspend.
6. Transfer 50 μl of the positive control mixture to the B1, resuspend.

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
1584d2
