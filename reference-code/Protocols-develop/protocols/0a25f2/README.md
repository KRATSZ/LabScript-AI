# Capsule Filling 3x Custom 10x10 Racks

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Tube Filling

## Description
This protocol dispenses a variable amount of oil from a source container in the usual location of the Opentrons trash bin to up to 300 capsules seated in 3 10x10 racks on the deck. The racks are filled in order of top left, then bottom left, then bottom right, depending on the number of samples. Within each rack, transfers are carried out down each column, then across each row. A single tip is used for the entire process

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* 3x Custom 10x10 capsule racks in custom Opentrons adapter
* [Opentrons 4-in-1 tuberack set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert holding [2ml Eppendorf snapcap tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [Opentrons P1000-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 1000ul tiprack](https://shop.opentrons.com/collections/opentrons-tips)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input your parameters for number of capsules to fill, transfer volume (in ul), and P1000 pipette mount side.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0a25f2
