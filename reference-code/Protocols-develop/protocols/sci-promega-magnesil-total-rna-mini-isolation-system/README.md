# Promega Magnesil Total RNA Mini Isolation System

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
     * Promega Kit

## Description

This protocol automates the paramagnetic bead-based purification of DNA-free total RNA for up to 96 samples using the [Promega Magnesil Total RNA Mini Isolation System](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/MagneSil+Total+RNA+mini-Isolation+System+TB328.pdf).

Links:
* [Promega Magnesil Total RNA Mini Isolation System](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/MagneSil+Total+RNA+mini-Isolation+System+TB328.pdf)

This protocol was developed to perform the following steps using the Promega Magnesil Total RNA Mini Isolation System: Bead binding, a wash step, DNAseI treatment and DNase inactivation, two additional washes followed by elution.

## Protocol Steps

Set up: Use settings in the OT app prior to running this protocol to pre-cool the temperature module to 4 degrees C. Elution plate (opentrons_96_aluminumblock_nest_wellplate_100ul) on the Temperature Module in deck slot 1, Reagent Reservoir (nest_12_reservoir_15ml) in deck slot 3 (DNase I in A1, DNase Inactivation in A2, wash1 (ethanol) in A3, wash2 (ethanol) in A4, wash3 (ethanol) in A5, elution buffer in A12), Deep Well Plate (nest_96_wellplate_2ml_deep) on the Magnetic Module in deck slot 6 (see setup detail below for samples and beads), Liquid Waste reservoir (nest_1_reservoir_195ml) in deck slot 9, Opentrons 200 ul filter tips in deck slots 2, 4, 5, 7, 8, 10 and 11.

The OT-2 will perform the following steps:
1. Binding- mix beads and input samples in wells of deep well plate on the Magnetic Module, engage magnets, transfer supernatants to liquid waste reservoir.
2. Wash1- transfer wash buffer from reagent reservoir to wells of the deep well plate on the Magnetic Module, mix beads with wash, engage magnets, transfer supernatants to the liquid waste reservoir.
3. DNAseI treatment transfer DNAseI to wells of deep well plate on the Magnetic Module, mix, pause to incubate.
4. DNase inactivation- transfer DNase inactivation buffer to wells of deep well plate on the Magnetic Module, mix, pause to incubate, engage magnets, transfer supernatants to liquid waste reservoir.
5. Wash2,Wash3 - transfer wash buffer from reagent reservoir to wells of the deep well plate on the Magnetic Module, mix beads with wash, engage magnets, transfer supernatants to the liquid waste reservoir.
6. Bead drying- pause to let beads air dry.
7. Elution- transfer elution buffer to wells of deep well plate on the Magnetic Module, mix, engage magnets, transfer eluate to elution plate held at 4 degrees on the Temperature Module.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/screenshot+deck+zack.png)

* Opentrons 200 ul filter tips (Deck Slots 2, 4, 5, 7, 8, 10, 11)
* Opentrons Temperature Module (cooled to 4 degrees C) with elution plate opentrons_96_aluminumblock_nest_wellplate_100ul (Deck Slot 1)
* Reagent Reservoir nest_12_reservoir_15ml (Deck Slot 3)
* Liquid Waste Reservoir nest_1_reservoir_195ml (Deck Slot 9)
* Opentrons Magnetic Module with deep well plate nest_96_wellplate_2ml_deep (Deck Slot 6)

![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/screenshot+reservoir.png)

![setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/screenshot+setup.png)

![setup2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/screenshot+setup2.png)

![data](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magnesil-total-rna-mini-isolation-system/data.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate number of samples (up to 96) using the parameters available on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-promega-magnesil-total-rna-mini-isolation-system
