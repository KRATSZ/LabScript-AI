# APIv2 PCR Prep: POOL

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep


## Description
This protocol consolidates the sample in a 96-well PCR plate into a 8-well PCR strip with the option to use the same tips.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P20 Multi-channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [10/20uL Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons aluminum block set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Bio-Rad Hard Shell 96-well PCR plate 200ul #hsp9601](bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Labcon 0.2mL PCR strips #3940-550](http://www.labcon.com/microstrips.html)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


Slot 1: Pre-Chilled [PCR Thermal Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with PCR strip placed in column 1 (empty)

Slots 2-5: 96-well PCR plate with samples from previous steps.

Slots 6-11: [10ul Opentrons tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters, specifically tip strategy (re-use tips or different tips for each transfer).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
This protocol is designed for preparing a 96-well sample and for use with the P20 Multi-channel pipette.

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
50486f-v2-part5
