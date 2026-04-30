# Custom Nucleic Acid Extraction and Bead Clean Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
     * Nucleic Acid Purification

## Description

This protocol automates the bead-based purification of nucleic acids from up to 96 cellular samples using a custom workflow.

Links:
* [Invitrogen DNA Binding Beads for MagMAX-96 DNA Multi-Sample Kit from ThermoFisher catalog number 4489112](https://www.thermofisher.com/order/catalog/product/4489112?SID=srch-srp-4489112#/4489112?SID=srch-srp-4489112)

This protocol was developed to perform the following steps: Bead binding, two wash steps, allow beads to air dry, followed by elution and transfer of the eluate to a fresh PCR plate.

## Protocol Steps

Set up: Elution plate (fully skirted 96-well PCR plate) in deck slot 1, Reagent Reservoir (12-well reservoir) in deck slot 2 (beads in A1, TE in A2, liquid waste will go in A3-A12), 50 mL Tube Rack with 50 mL Conical Tubes in deck slot 3, Deep Well Plate (96-deep well plate) on the Magnetic Module in deck slot 6, Opentrons 300 ul and 1000 ul tips in deck slots 4, 5, 7, 8, 9, 10 and 11. The protocol will calculate the number and location of 300 ul and 1000 ul tip boxes (to be displayed in the OT app during calibration and set up), and the volume of beads and TE needed to fill reservoir wells A1 and A2 and 70 percent ethanol to fill tubes A3 and B3 (the protocol run will pause and prompt the user to fill the reservoir and tubes with the needed volumes).

The OT-2 will perform the following steps:
1. Binding- add binding buffer to input samples in wells of deep well plate on the Magnetic Module, mix, engage magnets, transfer supernatants to liquid waste in reservoir A3-A12.
2. Wash1- transfer 70 percent ethanol from 50 mL tubes to wells of the deep well plate on the Magnetic Module, mix, engage magnets, transfer supernatants to the liquid waste tubes A3 and B3.
3. Wash2 - transfer 70 percent ethanol from 50 mL tubes to wells of the deep well plate on the Magnetic Module, mix, engage magnets, transfer supernatants to the liquid waste in reservoir A3-A12.
4. Bead drying- pause to let beads air dry.
5. Elution- transfer TE to wells of deep well plate on the Magnetic Module, mix, engage magnets, transfer eluate to elution plate in deck slot 1.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette and Single-Channel p1000 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 300 ul Tips and 1000 ul Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4b7268/layout.png)

* Opentrons 300 ul tips (Deck Slots 4,5,7 - depends on tip parking and sample count)
* Opentrons 1000 ul tips (Deck Slots 8,9,10 - depends on tip parking and sample count)
* Elution Plate (96-well PCR Plate) (Deck Slot 1)
* Reagent Reservoir (12-well reservoir) (Deck Slot 2)
* Opentrons 6-Tube Rack with 50 mL Conical Tubes opentrons_6_tuberack_falcon_50ml_conical (Deck Slot 3)
* Opentrons Magnetic Module with deep well plate (Deck Slot 6)


![liquids reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4b7268/reservoir_liquids.png)
![liquids tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4b7268/tubes_liquids.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate number of samples (up to 96), if parking tips (to use the same tips for bead mix and sup removal), and reservoir, deep-well, pcr plate labware using the parameters available on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b7268
