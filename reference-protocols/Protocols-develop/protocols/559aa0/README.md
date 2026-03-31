# PCR/qPCR prep: distribution of primers to 384-well plates

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * qPCR setup

## Description
This protocol automates the distribution of 4 different primers to the wells of up to nine 384-well plates in a specific arrangement shown in the attached plate map. The nine plates can be fully or partially filled (each plate filled to a different extent, as specified by choice of parameter values below prior to download of the protocol).

Links:
* [PCR/qPCR prep: distribution of patient samples to 384-well plates](http://protocols.opentrons.com/protocol/165a77)

* [plate map](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-08/e373l2s/384%20plate%20map.png)

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Using the parameters below, specify (as a comma-separated string of values each
between 1-12) the expected number of filled patient sample columns (anticipated
in the 96-well plates in the next downstream step) for each 384-well plate.
Also specify the number of 384-well plates to prepare and choose your 384-well plate labware.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

###### Internal
559aa0
