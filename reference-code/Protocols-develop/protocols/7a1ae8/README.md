# Zymobiomics Magbead Nucleic Acid Purification - v2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Kit

## Description
This protocol performs a custom nucleic acid purification using the Zymobiomics Magbead kit. This protocol was updated from [this](https://protocol-delivery.protocols.opentrons.com/protocol/0bdecb) to APIv2.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [NEST Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) or similar
* [Opentrons P300 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons P300 Multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 300ul tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**STARTING SETUP** for 4x6 2ml screwcap tube aluminum block (slot 2):
* tubes A1-D6: original samples (up to 24 samples aligned down columns and then across rows)

**MID-PROTOCOL SETUP** for 4x6 2ml screwcap tube aluminum block (slot 2):
* tubes A1-C1: molecular grade water tubes (1 tube for each 8 samples); *note-- the user is prompted to replace these tubes midway through the protocol*

12-channel reagent reservoir (slot 4):
* channel 1: mag binding buffer
* channel 2: magnetic beads
* channel 3: magwash 1
* channels 4-5: magwash 2 (1 channel each for 2x washes)

waste reservoir (slot 11):
* *Note-- the reservoir is programmed as an Agilent 290ml single-channel reservoir, but the user can replace this with any reservoir of choice for containing the liquid waste throughout the protocol by calibrating to the top of the reservoir before the run.*

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P300 single- ad multi-channel pipettes, the number of samples, and the volume of beads (in ul), the bead separation time (in minutes), and whether you are using a temperature module for drying.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7a1ae8
