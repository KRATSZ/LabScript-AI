# Patient Specimen (Saliva) Pooling 3:1 and 2:1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Pooling

## Description
This protocol uses two p1000-single channel (GEN2) pipettes to pool 500 ul aliquots of up to 96 patient samples to create up to 32 pools (when pool_size is specified in the parameters below as 3 samples combined) or up to 48 pools (when pool_size is specified in the parameters below as 2 samples combined) using an Opentrons OT-2 robot. This is a pythonized version (and modified to make use of two pipettes) of a [Protocol Designer protocol](https://designer.opentrons.com/). Sample racks are in deck slots 1, 3, 4, 6, 7, 9, and 10 and pool racks are in deck slots 2, 5, and 8 unless otherwise specified in the parameters below. 3:1 pools are kept apart on the deck to minimize risk of cross-contamination by leaving row "B" empty as much as possible. When more than 45 pools are created, column 5 of the last sample rack is used to locate the 46th, 47th and 48th pools.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P1000-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549142557)
* [Opentrons 1000ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [Opentrons 15 Tube Rack with Falcon 15 mL Conical](https://labware.opentrons.com/opentrons_15_tuberack_falcon_15ml_conical?category=tubeRack)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0175a4
