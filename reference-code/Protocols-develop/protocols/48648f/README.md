# Nucleic Acid Purification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Nucleic Acid Purification

## Description
This protocol automates the transfer of up to 90 patient samples to an extraction plate for the purification of nucleic acids using an Opentrons OT-2 robot. This is a pythonized version of a [Protocol Designer protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-01-27/jd23jyu/Sample%20Plating%2090%20samples.json). Each of the six patient sample racks should contain a full set of 15 samples.  Wells A1, B1, H1, A7, B7, and H7 in the extraction plate are left empty unless otherwise specified in the parameters below. The protocol transfers 100uL of each sample into a new well on the extraction plate using the custom tube rack and custom NEST well plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P1000-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549142557)
* [Opentrons 1000ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/products/tempdeck?_pos=1&_sid=5b80a3c66&_ss=r)
* [MTCbio 10 ml tube](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-01-27/jj43jf5/mtcbio_15_tuberack_10000ul.json)
* [NEST 96 2 mL](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-01-27/ox33jt1/nest_96_wellplate_2000ul.json)


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
48648f
