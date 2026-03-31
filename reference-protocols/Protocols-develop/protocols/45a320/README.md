# ReliaPrep™ Viral TNA Miniprep System, Custom

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
This protocol extracts DNA using the ReliaPrep™ Viral TNA Miniprep System extraction kit. Proteinase K, patient sample, cell lysis buffer and isopropanol are combined with a ReliaPrep Binding Column. After 3 washes, water is added to the column to form the eluate which can then be plated.  


Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples for this run. Samples should always be placed by column (A1, B1, C1,..,etc.).
* `P20/P1000 Dispense Flow Rate`: Global control of P20 and P1000 dispense flow rate. A value of 1.0 is default, 0.5 is 50% of the default flow rate, 1.2 is 20% faster the default flow rate, etc.
* `P20 Mount`: Specify which side (left or right) to mount the P20 single channel pipette.
* `P1000 Mount`: Specify which side (left or right) to mount the P1000 single channel pipette.


---

### Labware
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 1000ul Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons 20ul Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* Vacutainer tubes
* 1.5mL tubes


### Pipettes
* [P20 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

### Reagents
* [ReliaPrep™ Viral TNA Miniprep System, Custom](https://www.promega.com/products/nucleic-acid-extraction/viral-rna-extraction-viral-dna-extraction/reliaprep-viral-tna-miniprep-system-custom/?catNum=AX4820)


---

### Deck Setup

* On slot 2, empty tubes should be placed in every other column starting from column 1 (e.g. columns 1, 3, 5), which the protocol refers to when it pauses and prompts the user for instruction. Columns 2, 4, and 6 will be the binding column columns of the tube rack. Please see protocol steps below.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/45a320/Screen+Shot+2021-07-29+at+6.37.40+PM.png)

### Reagent Setup

* Reservoir: Slot 3
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/45a320/Screen+Shot+2021-07-26+at+4.16.01+PM.png)


---

### Protocol Steps
1. Pro-K added to all tubes up to the number of samples on the odd columns of slot 2.
2. Samples are added to odd columns on slot 2.
3. Cell lysis buffer is added to the odd columns on slot 2.
4. Incubate for 10 minutes with a pause at the end of incubation. User selects "Resume" when they have populated tubes with binding column up to the number of samples on the "right side" of the tube rack on slot 2.
5. Isopropanol is added, mixed, and contents are transferred from odd columns to "right" side on slot 2.
6. User is prompted to centrifuge
7. 3 wash steps with pauses which prompt the user to centrifuge. User puts empty tubes on the odd columns of the tube rack on slot 2.
8. Water is added to odd columns of the tube rack.
9. User places binding column in water
10. Water is added to binding column + water on odd columns

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
45a320
