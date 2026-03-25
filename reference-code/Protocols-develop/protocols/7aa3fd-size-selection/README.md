# NGS Prep Part 1/3: Size Selection

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Custom

## Description
This protocol performs the final size selection step of NGS library prep.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Eppendorf twin.tec 96-well PCR plate 150ul #0030128605](https://online-shop.eppendorf.com/OC-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-PF-8180.html)
* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/products/tube-rack-set-1?_ga=2.256255875.900706806.1575911292-1245111371.1550251253) with 4x6 insert for [2ml Eppendorf snapcap tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html) or equivalent.
* [Opentrons 10ul and 200ul filter tipracks](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons GEN1 P10 and P300 single-channel electronic pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 tuberack with 2ml Eppendorf snapcap tubes (slot 2)
* tube A1: SPRI beads
* tube B1-B3: 80% ethanol
* tube C1: Low EDTA TE

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process, bead mix volume (uL), bead mix speed (uL/s), bead mix repetitions, and the respective mount sides for your P10 and p300 single-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7aa3fd
