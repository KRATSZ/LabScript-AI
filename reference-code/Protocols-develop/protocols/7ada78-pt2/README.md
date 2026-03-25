# RNA Normalization I & II

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* Complete PCR Workflow

## Description
This protocol preps and runs a PCR on the Opentrons thermocycler using a .csv input. RNA and NF water are added to the PCR plate, and mastermix is then added to the resulting solution and mixed. A pause is included after the RNA is added to the water in the thermocycler plate, and the user is prompted to replace the water plate with the same 96 well plate, but with mastermix in column 1. If the protocol runs out of tips, it will automatically stop and the user is prompted to replace tips. For csv information and formatting notes, see below.


Explanation of complex parameters below:
* `Number of columns`: Specify the number of columns in the thermocycler plate to dispense mastermix into. Mastermix will always come from column 1 of the 96 well plate on slot 3. The mastermix plate will replace with water plate on slot 3 after an automatic pause in the protocol.
* `.CSV File`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line
(use slot 7 for the thermocycler slot, and input an "x" for values that are not needed in that row):
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1f62ba/Screen+Shot+2022-01-25+at+11.20.56+AM.png)
* `Pipette Mount`: Specify which mount (left or right) to host the P20 Single, and Multi-channel pipettes, respectively.

---

### Modules
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)


### Labware
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/verified-labware/well-plates/)
* [Opentrons 4-in-1 tube rack with 1.5mL Eppendoft snap cap tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 20ul Filter tips](https://shop.opentrons.com/universal-filter-tips/)
* 96-W Abgene Plate

### Pipettes
* [P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [P20 Multi-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7ada78/pt2/Screen+Shot+2021-12-22+at+5.17.44+PM.png)

### Reagent Setup
* Note that the water in slot 3 should be placed by column (A1, B1, C1, etc.) as the protocol will iterate through the water plate in this order as a source.

---

### Protocol Steps
1. Pre-cool thermocycler (TC) to 4C
2. Using single channel and based upon uploaded worklist, transfer x uL NF water from reservoir at slot 3 to appropriate wells of 96-well PCR plate nested w/in TC (e.g., 11 uL to well A1, 12 uL to well E7)
3. Repeat step 1 for all samples (up to 96)
4. Using single channel and based upon uploaded worklist, transfer y uL RNA from appropriate micro'fuge tube to appropriate wells of 96-well PCR plate nested w/in TC (e.g., 5 uL from slot 4 A1 => PCR plate well A1, 4 uL from slot 2 A1 => PCR plate well E7; note also that uL NF water + uL RNA = x + y = 16 uL).

Part B: RNA normalization II
1. Using multichannel and fresh tips for each destination column of wells, transfer 4 uL VILO Master Mix to each well of PCR plate, gently mix 4 times at 12uL.
2. Repeat step 1 for all columns of PCR plate, up to the number of columns specified.
3. Seal PCR plate, and execute TC protocol (25C for 10'', 50C for 10', 85C for 5').

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
7ada78-pt2
