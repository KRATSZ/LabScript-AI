# Plate Filling Heat Inactivated Covid Samples for PCR - Part 3

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps multiple 96 deep well plates with 600ul of saline up to the specified number of plates. All plates are fully filled with 600ul of saline. The left and right multi-channel pipettes aspirate and dispense two columns at a time. 

Explanation of complex parameters below:
* `Number of Plates`: Specify the number of plates to fill starting from slot 4.


---

### Labware
* [Opentrons 300ul tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 2mL 96 well deep well plate](nest_96_wellplate_2ml_deep)
* [NEST 195mL Reservoir](https://shop.opentrons.com/collections/reservoirs)


### Pipettes
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549142557)


---

### Deck Setup
* This is the deck setup for a run with 94 samples (bottom two rows of slot 11 are not populated).
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2df9f8/Screen+Shot+2021-09-29+at+10.02.57+AM.png)



---

### Protocol Steps
1. Saline is added to each well up to the number of wells psecified up to the number of plates specified starting from slot 4.

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
2df9f8-pt3
