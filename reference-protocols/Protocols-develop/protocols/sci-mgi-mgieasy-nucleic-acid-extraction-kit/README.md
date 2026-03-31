# MGI MGIEasy Nucleic Acid Extraction Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
     * MGI Kit

## Description

This protocol automates the magnetic bead-based purification of nucleic acids from throat swabs or bronchoalveolar lavage for up to 96 samples using the [MGI MGIEasy Nucleic Acid Extraction Kit](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-mgi-mgieasy-nucleic-acid-extraction-kit/MGIEasy+Nucleic+Acid+Extraction+Kit+User+Manual.pdf).

Links:
* [MGI MGIEasy Nucleic Acid Extraction Kit](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-mgi-mgieasy-nucleic-acid-extraction-kit/MGIEasy+Nucleic+Acid+Extraction+Kit+User+Manual.pdf)

This protocol was developed to perform the following steps using the MGI MGIEasy Nucleic Acid Extraction Kit: Sample lysis and bead binding, three wash steps, then elution of purified nucleic acids from the beads.

## Protocol Steps

Set up: Use settings in the OT app prior to running this protocol to pre-cool the temperature module to 4 degrees C. Elution plate (opentrons_96_aluminumblock_nest_wellplate_100ul) on the Temperature Module in deck slot 1, Reagent Reservoirs (nest_12_reservoir_15ml) in deck slots 2 (lysis buffer in columns 1-4, wash1 in columns 5-8, wash2 in columns 9-12) and 3 (wash3 in columns 1-4, elution buffer in column 12), Deep Well Plate (nest_96_wellplate_2ml_deep) on the Magnetic Module in deck slot 6, Liquid Waste reservoir (nest_1_reservoir_195ml) in deck slot 9, Opentrons 200 ul filter tips in deck slots 4, 5, 7, 8, 10, 11.   

The OT-2 will perform the following steps:
1. Lysis and binding- mix lysis buffer to suspend beads, transfer to wells of deep well plate on the Magnetic Module, mix, engage magnets, transfer supernatants to liquid waste reservoir.
2. Three wash steps- for each wash step, transfer wash buffer from reagent reservoir to wells of the deep well plate on the Magnetic Module, mix beads with wash, engage magnets, transfer supernatants to the liquid waste reservoir.
3. Bead drying- pause to let beads air dry.
4. Elution- transfer elution buffer to wells of deep well plate on the Magnetic Module, mix, engage magnets, transfer eluate to elution plate held at 4 degrees on the Temperature Module.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 200 ul Filter Tips for the p300 Pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-mgi-mgieasy-nucleic-acid-extraction-kit/layout.pdf)

* Opentrons 200 ul filter tips (Deck Slots 4, 5, 7, 8, 10, 11)
* Opentrons Temperature Module (cooled to 4 degrees C) with elution plate opentrons_96_aluminumblock_nest_wellplate_100ul (Deck Slot 1)
* Reagent Reservoirs nest_12_reservoir_15ml (Deck Slots 2, 3)
* Liquid Waste Reservoir nest_1_reservoir_195ml (Deck Slot 9)
* Opentrons Magnetic Module with deep well plate nest_96_wellplate_2ml_deep (Deck Slot 6)

![QC data](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-mgi-mgieasy-nucleic-acid-extraction-kit/QC+Data.pdf)

* For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate to the elution plate (well A1 is transferred to well A1, B1 to B1, etc.)
* If the tip parking feature is used (recommended), the protocol will conserve tips between reagent additiona and removal. Tips will be temporarily stored in tiprack wells corresponding to the well of the sample they access (tip parked in A1 will only be used for sample in A1). If not using the tip parking feature, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for higher throughput runs.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the parameter settings on this page to indicate number of samples (up to 96), if the tip parking feature should be used, and if the protocol should keep track of the starting tip for the next protocol run.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-mgi-mgieasy-nucleic-acid-extraction-kit
