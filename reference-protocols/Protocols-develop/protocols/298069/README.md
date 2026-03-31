# Sample Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Aliquoting

## Description
This protocol performs a custom sample aliquoting workflow by transferring the contents of 2 15ml tubes to 12 2ml tubes each. 300µl is transferred to each tube, and height tracking is performed automatically so that the pipette does not submerge into the solution in the 15ml tubes.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 3x5 insert for 15ml tubes
* [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 4x6 insert for 2ml tubes
* [Opentrons P1000 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549142557)
* [Opentrons 1000µl tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

3x5 tuberack for 15ml tubes (slot 1):
* tube A1: solution 1 (filled to at least 10ml mark)
* tube B1: solution 2 (filled to at least 10ml mark)

4x6 tuberack for 2ml tubes (slot 2):
* rows A and B: tubes to receive solution 1
* rows C and D: tubes to receive solution 2

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P1000 single-channel pipette, the number of capsules to fill, and the volume to fill each capsule (in ul).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
298069
