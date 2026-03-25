# Zymo Quick-DNA-RNA MagBead Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
     * Zymo Kit

## Description

This protocol automates the magnetic bead-based purification of DNA-free total RNA (if default protocol parameters are used at the time of protocol download to include the DNAseI step) or alternatively both DNA and total RNA from the same starting sample (both DNA and RNA in a combined single sample, if protocol parameters are used at the time of protocol download to skip the DNAseI step) for up to 96 samples using the [Zymo Quick-DNA-RNA MagBead Kit](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-quick-dna-rna-magbead/_r2130_r2131_quick-dna_rna_magbead.pdf).

Links:
* [Zymo Quick-DNA-RNA MagBead Kit](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-quick-dna-rna-magbead/_r2130_r2131_quick-dna_rna_magbead.pdf)

This protocol was developed to perform the following steps using the Zymo Quick-DNA-RNA MagBead Kit: Bead binding, 4 wash steps, DNAseI treatment (if preparing DNA-free total RNA), stop and elution. The default output sample is DNA-free total RNA. A protocol parameter (below) can be used at the time of protocol download to skip the DNAseI step for an output sample containing combined DNA and total RNA. Additional protocol parameters can be used at the time of protocol download to skip or include any of these steps (for testing purposes, for a partially manual and partially automated process, for a custom sequence of steps etc.)

## Protocol Steps

Set up: Use settings in the OT app prior to running this protocol to pre-cool the temperature module to 4 degrees C. Elution plate (opentrons_96_aluminumblock_nest_wellplate_100ul) on the Temperature Module in deck slot 1, Reagent Reservoirs (nest_12_reservoir_15ml) in deck slot 2 (Beads and Binding in A1,2; W1 in A3,4; W2 in A5,6; W3 in A7,8; W4 in A9,10; W5 in A11,12) and 3 (DNAseI in A1; Stop in A2-3, W6 in A4,5; Elution in A12), empty 200 ul filter tip rack (for parking tips) in deck slot 4, Deep Well Plate (nest_96_wellplate_2ml_deep) on the Magnetic Module in deck slot 6, Liquid Waste reservoir (nest_1_reservoir_195ml) in deck slot 9, Opentrons 200 ul filter tips in deck slots 5, 7, 8, 10 and 11.

The OT-2 will perform the following steps:
1. Binding- mix beads to suspend, transfer beads to wells of deep well plate on the Magnetic Module, pause for mixing in off-deck heater-shaker, engage magnets for 7 minutes, transfer supernatants to liquid waste reservoir.
2. Four wash steps- for each wash step, transfer wash buffer from reagent reservoir to wells of the deep well plate on the Magnetic Module, mix beads with wash, engage magnets for 7 minutes, transfer supernatants to the liquid waste reservoir.
3. DNAseI treatment (DNAseI step is for prep of DNA-free RNA, be sure to use protocol parameters below to skip DNAseI step for prep of combined DNA and total RNA sample)- transfer DNAseI to wells of deep well plate on the Magnetic Module, mix, pause to incubate with occasional mixing.
4. Stop reaction- transfer stop buffer to wells of deep well plate on the Magnetic Module, mix, pause to incubate 10 minutes with occasional mixing, engage magnets for 7 minutes, transfer supernatants to liquid waste reservoir.
5. Two Ethanol washes- transfer wash buffer from reagent reservoir to wells of the deep well plate on the Magnetic Module, mix beads with wash, engage magnets for 7 minutes, transfer supernatant to the liquid waster reservoir.
6. Bead drying- pause to let beads air dry.
7. Elution- transfer elution buffer to wells of deep well plate on the Magnetic Module, mix, engage magnets for 7 minutes, transfer eluate to elution plate held at 4 degrees on the Temperature Module.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/zymo-rna-extraction/Screen+Shot+2022-07-12+at+9.56.08+AM.png)

* Opentrons 200 ul filter tips (Deck Slots 5, 7, 8, 10, 11)
* empty Opentrons 200 ul filter tip box for parking tips (Deck Slot 4)
* Opentrons Temperature Module (cooled to 4 degrees C) with elution plate opentrons_96_aluminumblock_nest_wellplate_100ul (Deck Slot 1)
* Reagent Reservoirs nest_12_reservoir_15ml (Deck Slots 2, 3)
* Liquid Waste Reservoir nest_1_reservoir_195ml (Deck Slot 9)
* Opentrons Magnetic Module with deep well plate nest_96_wellplate_2ml_deep (Deck Slot 6)
![reagent layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/zymo-rna-extraction/Screen+Shot+2022-07-12+at+9.56.28+AM.png)


![data](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-quick-dna-rna-magbead/readme_data.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate number of samples (up to 96) and if including (for DNA-free Total RNA prep) or skipping (for combined DNA plus total RNA output sample) the DNAseI step using the parameters below. Any and all steps are customizable to be included or not.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-zymo-quick-dna-rna-magbead
