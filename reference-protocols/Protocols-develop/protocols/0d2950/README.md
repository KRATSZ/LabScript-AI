# Extraction Prep for TaqPath Covid-19 Combo Kit

### Author
[Opentrons](https://opentrons.com/)

### Partner
[appliedbiosystems](https://www.thermofisher.com/content/dam/LifeTech/Documents/PDFs/clinical/taqpath-COVID-19-combo-kit-full-instructions-for-use.pdf)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a sample plate with up to 95 samples (with one control). Samples in the tube rack should be placed to mirror the 96 well plate: column 1 (from the bottom up) of slots 1, 4, 7, and 10, then column two (from the bottom up of the same slots), up to column 5 of the aforementioned tube racks. Then column 1 of slots 2, 5, 8, 11 up to column 3 the tube racks in the aforementioned slots.

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples that will be processed. Up to 95 samples can be run, leaving room for a control.
* `P1000 sample tube aspiration height`: Specify the height (in mm) for the P1000 pipette to aspirate when visiting sample tubes. Default is 1mm.
* `P1000 sample dispense height (in plate)`: Specify the height (in mm) for the P1000 pipette to dispense from when visiting the plate on slot 3. Default is 1mm.
* `P1000 single GEN2 Mount`: Specify which mount (left or right) to load the P1000 single channel pipette.
---
### Labware
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons 1000uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons 4-in-1 tube rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)

### Pipettes
* [P1000 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

### Reagents
* [TaqPath Covid-19 Combo Kit](https://www.thermofisher.com/content/dam/LifeTech/Documents/PDFs/clinical/taqpath-COVID-19-combo-kit-full-instructions-for-use.pdf)

---

### Deck Setup
Example deck layout with 70 samples.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d2950/Screen+Shot+2021-10-11+at+11.12.37+AM.png)



---

### Protocol Steps
1. Pick up tip.
2. 200ul of sample is aspirated.
3. 200ul of sample is dispensed into deepwell plate, by column.
4. Drop tip.
5. Repeat up to the specified number of steps.



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
0d2950
