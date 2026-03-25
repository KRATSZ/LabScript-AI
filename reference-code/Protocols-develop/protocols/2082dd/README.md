# NGS Prep from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description
This protocol performs a NGS library prep through 2 fold dilutions and final pooling. All volumes are specified in a `.csv` file.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Bio-Rad Hardshell 96-well PCR plate 200ul #HSP9601](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons 4-in-1 tuberack with 4x6 insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Opentrons 4-in-1 tuberack with 3x5 insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) holding [15ml NEST centrifuge tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-15-ml-centrifuge-tube) or equivalent
* [Opentrons P20 and P300 GEN2 single-channel electronic pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20ul and 300ul tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

3x5 tuberack (slot 4)
* tube A1: TE buffer (filled to at least ~3cm below tube opening)

4x6 tuberack (slot 5)
* tubes A1: 1.5ml snapcap tube for pooling
* tube A2: 1.5ml screwcap tube for final pooled libraries

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P20 and P300 single-channel pipettes, and the input .csv file.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2082dd
