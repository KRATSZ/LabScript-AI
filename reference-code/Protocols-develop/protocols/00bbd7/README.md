# Covid-19 Saliva Sample Plating

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 96 well plate with Covid-19 saliva samples in up to 7 tube racks. Delays are inserted after aspiration to ensure the full volume of sample is achieved, as well as giving the user the ability to manipulate aspiration and dispense speeds.

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for this run.
* `Delay After Aspiration (seconds)`: Specify the number of seconds after aspirating Covid sample to allow time for the full volume to be achieved.
* `Aspiration/Dispense Speed`: Specify the speed at which to aspirate/dispense Covid sample. A value of 1 is the default speed, a value of 0.5 is half of the default speed, etc.
* `P1000 Single GEN2 Mount`: Specify whether the P1000 single channel pipette is on the left or right mount.


---


### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons 1000uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

### Pipettes
* [P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
Samples should be placed in tube racks by row (A1, A2, etc.) and by slot order 4, 5, 6, 7, 8, 9, 10.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00bbd7/Screen+Shot+2021-08-19+at+3.59.32+PM.png)

---

### Protocol Steps
1. Sample is aspirated from tube A1
2. Delay after aspirating
3. Sample dispensed into A1 of the 96 well plate
4. Sample is blown out of tip
5. Tip dropped, new tip achieved, repeat steps 1-4

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
00bbd7
