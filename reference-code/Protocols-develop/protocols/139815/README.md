# Pooling and Consolidation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Consolidation

## Description
This protocol performs a custom pooling and consolidation protocol from a 96-well PCR plate to an 8-tube strip, and then from the strip to a microcentrifuge tube.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Eppendorf twin.tec 96-well PCR plate 200ul](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-PF-8180.html) seated in aluminum block
* USA Scientific 12x8-tube strips 300ul seated in aluminum block
* [1.5ml Eppendorf safelock snapcap microcentrifuge tube](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html) seated in [Opentrons 4-in-1 tuberack with 4x6 microcentrifuge tube insert](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Opentrons GEN1 P10-single channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons GEN1 P300-single channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 10ul filter tip rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)
* [Opentrons 200ul filter tip rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

seated 8-tube strips (slot 2)
* strip 1: 8-tube strip for initial transfers from PCR plate

4x6 insert on Opentrons tuberack (slot 3)
* tube A1: tube for pooling

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P10 and P300 single-channel pipettes.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
139815
