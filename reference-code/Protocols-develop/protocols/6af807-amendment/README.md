# 384 Well Plate PCR Plate with Triplicates

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 384 well plate for up to 8 cDNA samples in triplicates. The protocol can be broken down into 2 main parts:

* cDNA is added in triplicates down the column onto the plate.
* Mastermix is added to the cDNA.

Explanation of complex parameters below:
* `Number of cDNA`: Specify the number of cDNA tubes that will be loaded onto the tube rack.
* `Number of mastermix tubes`: Specify the number of mastermix tubes that will be added to the cDNA.
* `cDNA/mastermix volume`: Specify the volume of both the cDNA and mastermix. Note, the mastermix volume will be calculated from this volume (total 20ul).
* `P20 Mount`: Specify the mount (left or right) for the P20 single channel pipette.

---

### Labware
* [Thermofisher 384 well plate](https://www.thermofisher.com/order/catalog/product/4309849#/4309849)
* [Opentrons 24 tube rack with 1.5mL Eppendorf tubes](opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap)
* [Opentrons 20ul Tips](opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap)

### Pipettes
* [P20 Single Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* Note: Mastermixes and cDNA tubes should be placed on their respective tube racks by column. Please look at the deck layout below for a full run (8 genes and 16 mastermixes).


![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6af807/Screen+Shot+2023-08-03+at+2.05.09+PM.png)


---

### Protocol Steps
1. cDNA is transferred in triplicates down a column up to the number of columns as specified in number of mastermixes.
2. Mastermixes are added to each column up to each populated row.

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
6af807
