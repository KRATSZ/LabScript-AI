# Syber Green PCR Prep with Cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* Syber Green Prep

## Description

This protocol performs a custom Syber Green PCR Prep for up to 96 samples. Mastermix is transferred from 1.5ml Eppendorf tubes, and samples are transferred from source strip tubes mounted in the Opentrons 96-well aluminum block into the MicroAmp PCR plate also mounted in the Opentrons 96-well aluminum block.

The input .csv file should be formatted in the following way, including the header line:

```
source well (A1-H12),mastermix tube (A1-D6),destination well (A1-H12)
A1,A1,A1
A2,A2,A2
...
```

---

### Labware
* [ThermoFisher MicroAmp™ Fast Optical 96-Well Reaction Plate with Barcode, 0.1 mL #4346906](https://www.thermofisher.com/order/catalog/product/4346906)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 4-in-1 tuberack with 4x6 insert](https://shop.opentrons.com/4-in-1-tube-rack-set/) for 1.5ml Eppendorf tubes
* [Opentrons 96-well aluminum block](https://shop.opentrons.com/aluminum-block-set/)

### Pipettes
* [P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup

* green: starting DNA samples
* blue: possible positions for mastermixes  
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/85b0dc/deck.png)

---

### Protocol Steps
1. The user-specified volume of mastermix is transferred to the final PCR plate according to user `.csv` input.
2. The user-specified volume of DNA sample is transferred to the final PCR plate with pre-added mastermix according to user `.csv` input.

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
85b0dc
