# Semi-Automated PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol first preps one 384 well plate with lysis buffer and sample to undergo a thermocycler. In this step, samples are transferred from tube rack to the 384 well plate. If the number of samples selected exceeds the number of samples that can fit onto the deck, the protocol pauses and prompts the user to refill the tube racks with new samples up to the number of samples selected. Afterwards, 4ul of the resulting solution is transferred to the final 384 well plate.

Explanation of complex parameters below:
* `Number of Samples`: Select the number of samples (1-384) for this run. If larger than 90 samples are selected, the protocol will pause after the last sample is transferred on the deck and will prompt the user to refill samples up to the number specified. Samples should always be placed in the tuberack down by column, and in the order of the deck slots (i.e. 4, 5, 6 ..., etc.)
* `P20/P300 Dispense Flow Rate`: Global control of P20 and P300 dispense flow rate. A value of 1.0 is default, 0.5 is 50% of the default flow rate, 1.2 is 20% faster the default flow rate, etc. 
* `P20 Single Mount`: Specify whether the P20 single channel pipette will be mounted on the left or right.
* `P300 Single Mount`: Specify whether the P300 single channel pipette will be mounted on the left or right.


---

### Labware
* Custom 384 well plate
* [Opentrons 4-in-1 tube rack with 15 tube insert](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 200ul filter tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 20ul tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Nest 12 Well Reservoir, 195mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [P20 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup
* Deck map with lysis buffer in A1 (first well) of the Nest 12 well reservoir.

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5c50d9/Screen+Shot+2021-08-26+at+3.26.46+PM.png)

---

### Protocol Steps
1. 50ul of lysis buffer is added to relevant wells on 384 well plate 1 (same tip).
2. 50ul of sample is added to relevant wells on 384 well plate 1 (different tip).
3. Protocol pauses for offline thermocycling
4. 4ul of resulting solution transferred to 384 well plate 2.


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
5c50d9
