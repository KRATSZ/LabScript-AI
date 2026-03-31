# BioGX XFree RT-PCR Reaction Setup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * PCR Prep

## Description

This protocol uses a p20 multi-channel pipette to distribute (15 uL by default, or optionally 10 uL) BioGX XFree mastermix [BioGX XFree Mastermix](https://www.biogx.com/xfree/) from columns of a 96-well plate held at 4 degrees on an Opentrons Temperature Module to columns of a reaction plate (either 96 or 384-well plate) on a second Opentrons Temperature Module also at 4 degrees. The p20 multi is then used to transfer 5 uL viral RNA input sample (sample count can be anywhere between 1 and 384 samples) from up to four 96-well sample plates to the reaction plate wells containing mastermix.

## Protocol Steps

This protocol is for part-2 of a two-step process. The input viral RNA samples for this protocol (up to four elution plates output from part-1) were prepared using:
* [automated OT-2 protocol from the Opentrons Protocol Library - Mag-Bind® Viral DNA/RNA 96 Kit](https://protocols.opentrons.com/protocol/sci-omegabiotek-magbind)
* [reagent kit - Omega Mag-Bind® Viral DNA/RNA 96 Kit - 12 x](https://shop.opentrons.com/collections/verified-reagents/products/omega-mag-bind-viral-dna-rna-96-kit-12-x-96-preps)

Set up: Be sure to use the left USB port to connect the Temperature Module located in deck slot 1. Be sure to use the right USB port to connect the Temperature Module located in deck slot 3. Precool both temperature modules to 4 degrees C by using settings in the OT app prior to running this protocol. Place up to four sample plates (96-well elution plates from the step 1 - extraction of viral RNA) in deck slots 2, 4, 5, 6 (in that order). Place the mastermix plate (with one column already filled for each full plate of 96 input samples, so there would be four columns filled for 384 input samples - 180 uL mastermix per well if mastermix transfer volume is 15 uL, 120 uL per well if 10 uL). Place the 96-well or 384-well reaction plate on the appropriate aluminum block on the Temperature Module in deck slot 3. Place Opentrons 20 uL filter tips opentrons_96_filtertiprack_20ul in deck slots 7-11.

The OT-2 will perform the following steps:
1. Use the p20 multi to distribute mastermix (15 uL per well by default, optionally 10 uL per well) to the reaction plate (either 96-well or 384-well format) according to the number of input viral RNA samples specified.
5. Use the p20 multi to transfer (5 uL per well) input viral RNA sample to columns of the reaction plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips for the p20 Pipette](https://shop.opentrons.com/collections/opentrons-tips)
* [BioGX XFree Mastermix](https://www.biogx.com/xfree/)
* [384-well Aluminum Block]()

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1e744e/layout.png)

* Opentrons 20ul filter tips (deck slots 7-11)
* Reaction Plate 96-well PCR plate (on Temperature Module deck slot 1)
* Mastermix Plate 96-well PCR Plate (on Temperature Module deck slot 3)
* Sample Plates 96-well PCR Plates (deck slots 2, 4, 5, 6)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameters on this page to make any needed adjustment to: decision to include or skip the mastermix distribution step (included by default), include or skip the sample transfer step (included by default), the number of input samples (1-384), the labware items to be used, the transfer volume of mastermix (default 15 uL), and well bottom clearances (minimum distance in millimeters between the tip and the bottom of the tube or well).
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1e744e
