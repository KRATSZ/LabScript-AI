# Plate Filling Heat Inactivated Covid Samples for PCR - Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 96 well plate by transferring 6ul from a source plate deepwell plate to a destination deepwell plate.

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples (1-94) to run on this protocol. Note: samples will be picked by row in the tube racks, in order of slots 7, 8, 10, and 11.
* `P20 Mount`: Specify which side to mount your P20 Multi Channel Pipette.

---

### Labware
* [Opentrons 20ul tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)


### Pipettes
* [P20 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)


---

### Deck Setup
* This is the deck setup for a run with 94 samples (bottom two rows of slot 11 are not populated).
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2df9f8/Screen+Shot+2021-09-29+at+10.02.24+AM.png)



---

### Protocol Steps
1. 6ul of solution is transferred from column 1 of the source plate to the destination plate.

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
2df9f8-pt2
