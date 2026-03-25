# Dilution with CSV File and Custom Tube Rack

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol transfers sample and diluent to a custom 40 tube rack on the temperature module. Liquid height is tracked in the diluent tube rack, and the temperature module is set to 4C. A fresh tip is granted for each diluent and sample transfer, and mixed after sample is dispensed.

Explanation of complex parameters below:
* `input .csv file`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line:
```
Diluent Transfer Volume (ul), Dispense Tube (rack), Source Well, Sample Transfer Volume
1000, A1, A1, 20
```
* `Track tips?`: Specify whether to start at A1 of both tip racks, or to start picking up from where the last protocol left off. 
* `Initial Volume Diluent (mL)`: Specify the initial volume of diluent in A1 of the 6 tube rack.
* `P20/P1000 Mounts`: Specify which mount (left or right) to host the P20 and P1000 pipettes.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Opentrons 6 Tube Rack with NEST 50 mL Conical](https://labware.opentrons.com/opentrons_6_tuberack_nest_50ml_conical?category=tubeRack)
* [NEST 96 Well Plate Flat](https://shop.opentrons.com/nest-96-well-plate-flat/)
* [Opentrons 20ul Tips](https://shop.opentrons.com/universal-filter-tips/)
* [Opentrons 1000ul Tips](https://shop.opentrons.com/universal-filter-tips/)
* Custom 40 Tube Rack

### Pipettes
* [P20 Single-Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [P1000 Single-Channel Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-bms/Screen+Shot+2022-04-19+at+2.35.41+PM.png)

---

### Protocol Steps
1. Diluent is added to the final tube rack in slot 1 per the csv input. Change tips to account for low viscosity.
2. Sample is added to the final tube rack in slot 1 per the csv input. Change tips to avoid cross contamination.
3. Sample and diluent is mixed after dispensing sample.

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
onsite-bms
