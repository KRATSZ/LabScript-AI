# Variable Slide Dispensing

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol spots up to 6 slides with antibody. Each slide has 8 wells, to which the protocol will spot with 8 dots for wells 2-7. The user has the ability to manipulate the spacing between the dots, as well as the volume of the dispenses. The user can also specify the number of slides spotted. Please see below for the order in which slides are spotted.

Explanation of complex parameters below:
* `Number of tubes`: Specify the number of tubes this protocol will run.
* `Number of Slides`: Specify the number of slides for this run (1-6).
* `Spot Spacing`: Specify the spacing between dots on the slide wells.
* `Spot Volume`: Specify the volume of each dot.
* `Aspiration Flow Rate`: Specify the aspiration rate. A value of 1 is the default rate, a value of 1.2 is a 20% increase of the default rate, a value of 0.5 is half of the default rate.
* `Dispense Flow Rate`: Specify the dispense rate. A value of 1 is the default rate, a value of 1.2 is a 20% increase of the default rate, a value of 0.5 is half of the default rate.
* `P20 Single-Channel Mount`: Specify which mount (left or right) to host the P20 single-channel pipette.




---


### Labware
* [Opentrons 10ul filter tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 tube rack with Eppendorf 1.5mL safelock snapcap](https://shop.opentrons.com/collections/racks-and-adapters)
* Custom slide plate

### Pipettes
* [P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0045f1/Screen+Shot+2021-11-10+at+5.49.36+PM.png)


---

### Protocol Steps
1. Pipette will aspirate user-specified volume from tube 1, and dispense into the top-left spot on every other well starting from the second, for all slide plate positions.
2. Pipette will aspirate user-specified volume from tube 2, and dispense into the bottom-left spot on every other well starting from the third, for all slide plate positions.
3. Repeat until all slides are filled.

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
0045f1
