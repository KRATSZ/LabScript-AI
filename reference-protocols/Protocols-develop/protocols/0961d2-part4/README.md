# plexWell LP384 Part 4

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* plexWell LP384


## Description
This protocol is part 4 of a 4-part protocol designed to accomplish the Sample-Barcoding Module of the [plexWell 384 Low Pass Library Preparation](https://seqwell.com/products/plexwell-lp-384/).


[Part 1](https://protocols.opentrons.com/protocol/0961d2-part1)
[Part 2](https://protocols.opentrons.com/protocol/0961d2-part2)
[Part 3](https://protocols.opentrons.com/protocol/0961d2-part3)
[Part 4](https://protocols.opentrons.com/protocol/0961d2-part4)


This protocol performs the second half of Step 3 (SB Pooling). During this protocol, each column of the destination plate in [Part 3](https://protocols.opentrons.com/protocol/0961d2-part3) is pooled into a 2mL DNA LoBind tube. The user has the option to pool up to 12 columns (the entire plate) into individual tubes for each column.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300 Single Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Bio-Rad 96-Well Plate, 200µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate), containing samples from [Part 3](https://protocols.opentrons.com/protocol/0961d2-part3)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 24 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [2mL DNA LoBind Tubes](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap?category=tubeRack)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons 200µL Filter Tips

Slot 2: *Empty*

Slot 3: Bio-Rad Plate, containing samples

Slot 4: *Empty*

Slot 5: *Empty*

Slot 6: Tube Rack with 2mL Tubes


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0961d2-part4
