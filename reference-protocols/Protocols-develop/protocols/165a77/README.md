# PCR/qPCR prep: distribution of patient samples to 384-well plates

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * qPCR setup

## Description
This protocol automates the distribution of patient samples to the wells of up to three 384-well plates in a specific arrangement shown in the attached plate map. The number of columns filled with patient sample for each plate can be specified (as a single comma-separated string of values between 1 and 12 like "8,8,12") in the parameters below.

Links:
* [PCR/qPCR prep: distribution of primers to 384-well plates](http://protocols.opentrons.com/protocol/559aa0)

* [plate map](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-08/e373l2s/384%20plate%20map.png)

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)


## Process
1. Choose the number of patient sample plates, the number of columns filled with patient sample for each plate, and your 384-well plate labware, and the pipette disposal volume if any (default is set to 1 ul) using the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

###### Internal
165a77
