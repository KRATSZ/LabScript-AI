# Plate Loading for ddPCR

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * PCR Prep

## Description

This protocol uses a p20 single channel pipette to load (in triplicate) up to four 96-well plates (loading of each plate will be finished before loading of the next plate is started) in preparation for ddPCR from 2 mL source tubes containing reagent mix, water, up to 27 template samples and a positive control template sample (CSV-formatted plate maps are uploaded at the time of protocol download to specify the location and number of sample and control tubes).

Links:
* [SOP_SARS-CoV2 in sewage Rose Lab_MSU_v2021draft_06.18.21](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-06-22/ux22lt2/SOP_SARS-CoV2%20in%20sewage%20Rose%20Lab_MSU_v2021draft_06.18.21.pdf)
* [Sample Plate Map CSV File](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3b3d2f/N1N2+duplex+plate+map.csv)
* [Sample Plate Map CSV File](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3b3d2f/Phi6+simplex+plate+map.csv)

This protocol was developed to perform the ddPCR plate loading part of the attached SOP for up to four ddPCR plates according to uploaded plate maps formatted as seen in the attached examples (based on plate map examples from Appendix A of the attached SOP).

## Protocol Steps

Set up: User should set OT app settings to pre-chill the temperature block to 4 degrees C in advance prior to the protocol run. 2 mL NEST snap cap tubes in the pre-chilled (4 degrees C) temperture module in slot 3 containing (in column order like A1-D1, A2-D2 etc.) one tube of reaction mix, one tube of water, up to 27 samples, and one positive control sample. Destination plate (ddPCR plate being loaded) in slot 5, p20 filter tips in slots 10 and 11.

The OT-2 will perform the following steps:
1. p20s transfer 16.5 ul reaction mix to the ddPCR plate columns specified in the plate map to receive liquids. The plate map will always specify a number of full columns (ddPCR process requires full columns).
2. p20s transfer 5.5 ul water to three wells designated as NTC in the plate map.
3. p20s transfer 5.5 ul of each of up to 27 samples in triplicate as specified in the plate map. If the sample count exceeds the capacity of the temperature block, the OT-2 will pause at the right time to allow loading of the remaining samples into the block.
4. p20s transfer 5.5 ul positive control sample to three designated wells in the plate map.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3b3d2f/layout_3b3d2f.png)

* Opentrons p20 filter tips (Deck Slots 10, 11)
* Opentrons Temperature Module (with opentrons_24_aluminumblock_nest_2ml_snapcap Deck Slot 3)
* ddPCR Plate (biorad_96_wellplate_200ul_pcr Deck Slot 5)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your input CSV files (one plate map for each ddPCR plate to be loaded, up to 4 in total) using the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3b3d2f
