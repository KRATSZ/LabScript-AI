# Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec

## Description
This protocol performs a custom mass spec sample prep for up to 20 samples.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons temperature module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [NEST 96-well PCR plate 100µl full skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [4x6 aluminum block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set) for [NEST 1.5ml snapcap tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [Opentrons 20µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 300µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons P20 and P300 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 aluminum block for NEST 1.5ml snapcap tubes (slot 2)
* tube D1: denaturing solution
* tube D2: DTT
* all other tubes: samples that will be transferred to their corresponding locations in sample plate

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P300 single-channel pipette, P20 single-channel pipette, and the number of samples.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
459a55
