# Anti-PEG ELISA

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Plate Filling

## Description

This protocol uses a p300 multi-channel and p300 single-channel pipette to transfer up to 57 samples plus serial dilutions of IgG, IgM and IgE standards to 384-well ELISA plates.

Links:
* [plate layout and process steps](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-06-27/gp23j3n/OT-2%20APA%20ELISA%20Protocol.zip)

This protocol was developed to transfer up to 57 samples from eppendorf tubes in 24 tube racks to 96-well sample prep plates, then transfer and serially dilute IgG, IgM and IgE standards in a sample prep plate, followed by transfer of samples and serial dilutions to three 384-well ELISA plates. The sample arrangment for the tube racks, sample prep plates and ELISA plates is shown in the attached excel spreadsheet.

## Protocol Steps

Set up: 24 tube racks containing up to 57 initial samples in deck slots 1, 4 and 7. 96-well sample prep plates in deck slots 2 and 5. 384-well ELISA plates in deck slots 3, 6 and 9. p300 tips in slots 10 and 11.

The OT-2 will perform the following steps:
1. transfer samples to sample prep plates in duplicate (arrangement shown in attached excel spreadsheet)
2. transfer IgG, IgM and IgE standards and make serial dilutions in the sample prep plate (arrangement shown in attached excel spreadsheet)
3. transfer the samples and serial dilutions to three 384-well ELISA plates (arrangment shown in attached excel spreadsheet)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/39bbbb/layout_39bbbb.png)

* Opentrons p300 tips (Deck Slots 10, 11)
* ELISA plates thermo_384_wellplate_50ul (Deck Slots 3, 6, 9)
* Sample prep plates 96-well plates (Deck Slots 2, 5)
* opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap (Deck Slots 1, 4, 7)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate the sample count, labware choices and well bottom clearances for the process steps using the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
39bbbb
