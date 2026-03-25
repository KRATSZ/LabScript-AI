# plexWell LP384 Part 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* plexWell LP384


## Description
This protocol is part 1 of a 4-part protocol designed to accomplish the Sample-Barcoding Module of the [plexWell 384 Low Pass Library Preparation](https://seqwell.com/products/plexwell-lp-384/).


[Part 1](https://protocols.opentrons.com/protocol/0961d2-part1)
[Part 2](https://protocols.opentrons.com/protocol/0961d2-part2)
[Part 3](https://protocols.opentrons.com/protocol/0961d2-part3)
[Part 4](https://protocols.opentrons.com/protocol/0961d2-part4)


This protocol accomplishes Step 1 (Sample-Barcoding, SB, Reaction Set-up). During this protocol, 6µL of input DNA in each well of two 96-well plates is transferred to the SBP96 plate containing specific reagents. 5µL of Coding Buffer (3X) is then added to each well of the SBP96 plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [plexWell LP 384 Kit](https://seqwell.com/products/plexwell-lp-384/)
- SBP96 Plate
- Coding Buffer (3X)
* [Opentrons P10 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Bio-Rad 96-Well Plate, 200µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate), containing samples
* [NEST 12-Well Reservoir, 15mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* [Opentrons 10µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons 10µL Filter Tips

Slot 2: Bio-Rad Plate, containing samples (Source 1)

Slot 3: SBP96 Plate (Destination 1)

Slot 4: Opentrons 10µL Filter Tips

Slot 5: Bio-Rad Plate, containing samples (Source 2)

Slot 6: SBP96 Plate (Destination 2)

Slot 7: Opentrons 10µL Filter Tips

Slot 8: *Empty*

Slot 9: Nest 12-Well Reservoir
* Column 1: Coding Buffer (3X)

Slot 10: Opentrons 10µL Filter Tips


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
0961d2-part1
