# COVID-19 Diagnostic Workflow: Assay 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
    * RNA Extraction

## Description
This protocol is a full COVID-19 diagnostic workflow up to RNA amplification. Samples are loaded in 15ml tubes and transferred to 1.5ml tubes for lysis and temperature incubations on an Opentrons temperature module. The samples are then transferred to a deepwell plate mounted on an Opentrons magnetic module for a 1-wash magnetic bead-based RNA extraction.

Explanation of protocol parameters below:
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)  

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons magnetic module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons temperature module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [USA Scientific PlateOne 96 Deepwell Plate 2mL](https://www.usascientific.com/plateone-96-deep-well-2ml/p/PlateOne-96-Deep-Well-2mL)
* [Opentrons 96 Filter Tip Rack 200 and 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons P300-Multi GEN2 and P1000-Single GEN2 electronic pipettes](https://shop.opentrons.com/collections/ot-2-pipettes)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)  

![setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/747d99/setup.png)  

Reservoir (slot 2):
* channel 1: lysis and hybridization buffer (HB1)
* channel 2: magnetic beads
* channel 4: wash buffer
* channel 5: master mix
* channel 12: liquid waste (loaded empty)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select your protocol parameters.
2. Download your protocol package.
3. Upload your custom labware and protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
747d99
