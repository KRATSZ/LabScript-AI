# 76ab0e: Temperature controlled normalization from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol is based on the [ML_normalization protocol](https://protocols.opentrons.com/protocol/ML-normalization) and it performs a custom sample normalization from a source PCR plate to a second PCR plate, diluting with diluent (e.g. buffer or water) from a reservoir. Sample and diluent volumes are specified via .csv file in the following format, including the header line (empty lines ignored):

```
source plate well,destination plate well,volume sample (µl),volume diluent (µl)
A1, A1, 2, 28
```

Diluent is transferred first from the 12 well reservoir to the target plate wells as specified in the csv using the same pipette tip. After finishing, the pipette(s) drop their/its tip(s) and transfer samples to the target wells.

This protocol loads the sample and destination plate on 2nd generation temperature modules

Explanation of parameters below:
* `input .csv file`: Here, you should upload a .csv file formatted as described above.
* `P20 GEN2 mount`: Choose whether to load the p20 in the right or left mount
* `P300 GEN2 mount`: Choose whether to load the p300 in the right or left mount
* `Aspiration height from bottom of the plate wells [mm]`: Offset to aspirate from the bottom of the source plate wells (in units of mm)
* `Dispensing height from bottom of the plate wells [mm]`: Offset for dispenses from the bottom of the destination plate wells (in units of mm)
* `Aspiration height from bottom of the reservoir wells [mm]`: Offset to aspirate from the bottom of the reservoir wells (in units of mm)
* `Flow rate multiplier`: By setting this multiplier to a value 0 < x < 1 the rate of sample aspiration and dispensing will be slowed down. The default value is 0.5 resulting in aspiration at half of the regular speed.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Aluminum Block Set](https://shop.opentrons.com/aluminum-block-set/)
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 12 well 15 mL reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)

### Pipettes
* [Single channel 20 uL pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Single channel 300 uL pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
This protocol may be used with the following kit, but it can be used with any samples and diluents
* [M-PER™ Mammalian Protein Extraction Reagent](https://www.thermofisher.com/order/catalog/product/78501)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76ab0e/deck.jpg)

### Reagent Setup
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76ab0e/reservoir.jpg)
* 12 well reservoir on slot 2: Add 15 mL of diluent per well to be used (well 1 up to 4)

---

### Protocol Steps
1. Pick up tips.
2. Aspirate diluent from from one of well 1-4 in the Nest 12 channel 15 ml reservoir in slot 2.
3. Transfer diluent to all the specified wells of the destination 96-well plate according to the csv file. The height to aspirate from the bottom of the well is controlled by a parameter.
4. Repeat step 2 and 3 using the same tip until diluent transfer is completed for all specified destination wells.
5. Dispense the tip in the Trash.
6. Pick up tips (using 20 ul pipette for 1-20 ul range, and 300 pipette for 1-200 ul range).
7. Aspirate sample from the csv specified well of the source 96-well plate (the rate of aspiration is controlled by the `Flow rate multiplier` parameter and is set to 0.5 by default i.e. half of the regular rate).
8. Transfer samples from the specified well of the source 96-well plate to the specified well of the destination 96-well plate.
9. Dispense the tip in the Trash.
10. Repeat step 7, 8 and 9 until the sample transfer is finished for all the specified wells.


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
76ab0e
