# Quarter Volume (modified) NEBNext Ultra II FS DNA Library Prep Kit for Illumina Part 2 of 3

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II FS DNA Library Prep Kit for Illumina

## Description
Part 2 of 3: Clean Up and PCR Enrichment.

Links:
* [Part 1: End Prep and Adapter Ligation](http://protocols.opentrons.com/protocol/3fad82)
* [Part 2: Clean Up and PCR Enrichment](http://protocols.opentrons.com/protocol/3fad82-part-2)
* [Part 3: Final Clean Up](http://protocols.opentrons.com/protocol/3fad82-part-3)

With this protocol, your robot can perform a modified Quarter Volume NEBNext Ultra II FS DNA Library Prep Kit for Illumina protocol described by the [Experimental Protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-05-07/ia13rz0/Quarter%20volume%20NEB%20Next%20Ultra%20II%20DNA%20Library%20Prep%20Kit%20for%20Illumina.docx). [NEB Instruction Manual for NEBNext](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-05-07/ce23ruu/manualE7805.pdf).

This is part 2 of the protocol: Clean up and PCR enrichment.

This protocol assumes up to 96 input samples and follows the attached experimental protocol.

After the steps carried out in this protocol (part 2), proceed with part 3: Final Clean Up.


## Protocol Steps

Set up: See the attached experimental protocol.

The OT-2 will perform the following steps:
1. Bead based clean up, wash and elute.
2. Transfer eluate to PCR plate containing master mix.
2. Run PCR cycling steps on the thermocycler module.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p300 and p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons p20 tips (Deck Slots 2,3,5)
* Opentrons p300 tips (Deck Slot 6)
* Opentrons Thermocycler Module (Deck Slots 7,8,10,11)
* Opentrons Magnetic Module with Sample Plate (Deck Slot 4)
* Reagent Reservoir (Deck Slot 1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 96)", choice of p20 and p300 tips, "Choice of PCR Plate", well-bottom clearance, flow rate, and magnet engage height and engage time in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3fad82-part-2
