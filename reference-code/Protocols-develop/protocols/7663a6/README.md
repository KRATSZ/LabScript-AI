# PCR Prep with Frozen Aluminum Block

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 96 well plate by column with mastermix and sample. Mastermix is held in an Opentrons 24-tube aluminum block without the temperature module. The aluminum block is placed in the freezer prior to running to keep mastermix cool.


Explanation of complex parameters below:
* `Number of Columns`: Input number of sample columns for this run.
* `Source Plate Starting Column`: Specify the source plate starting column for samples.
* `Destination Plate Starting Column`: Specify the destination plate starting column.
* `Sample Volume (ul)`: Specify sample volume in ul.
* `Mastermix Volume (ul)`: Specify mastermix volume in ul.
* `Source Aspiration Height (Plate)`: Specify aspiration height (in mm) from the bottom of the well in the sample plate.
* `Source Aspiration Height (Tube)`: Specify aspiration height (in mm) from the bottom of the tube in the mastermix tube.
* `Source Aspiration Flow Rate Sample (ul/sec)`: Specify the aspiration flow rate for sample.
* `Delay After Aspiration Mastermix (seconds)`: Specify the delay after aspirating mastermix in the tube. This may be helpful with viscous liquids, allowing the pipette time to achieve the full volume before moving on.
* `Source Aspiration Flow Rate Mastermix (ul/sec)`: Specify the aspiration flow rate for mastermix.
* `Dispense Height (from bottom)`: Specify dispense height (in mm) from the bottom of the well in the destination plate.
* `Dispense Flow Rate Sample`: Specify the dispense flow rate of sample into destination plate.
* `Dispense Flow Rate Mastermix`: Specify the dispense flow rate of mastermix into destination plate.
* `Mix Repetitions`: Specify number of mix steps.
* `Touch Tip?`: Specify whether to include touch tip in this run.
* `Blowout?`: Specify whether to include blow out in this run.
* `P20 Single Mount`: Specify left or right mount for the P20 single.
* `P20 Multi Mount`: Specify left or right mount for the P20 multi.




---

### Labware
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

### Pipettes
* [P20 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P20 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)


---

### Deck Setup
* Deck Setup running 10 columns. Mastermix is held in A1 of the tube rack on Slot 3.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/Screen+Shot+2021-06-29+at+11.23.20+AM.png)

---

### Protocol Steps
1. Mastermix is added to the plate up to the number of columns specified (single channel pipette).
2. Samples are added to the plate up to the number of columns specified (multi-channel pipette).
3. Samples + mastermix are mixed as specified.

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
7663a6
