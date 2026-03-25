# plexWell LP384 Part 3

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* plexWell LP384


## Description
This protocol is part 3 of a 4-part protocol designed to accomplish the Sample-Barcoding Module of the [plexWell 384 Low Pass Library Preparation](https://seqwell.com/products/plexwell-lp-384/).


[Part 1](https://protocols.opentrons.com/protocol/0961d2-part1)
[Part 2](https://protocols.opentrons.com/protocol/0961d2-part2)
[Part 3](https://protocols.opentrons.com/protocol/0961d2-part3)
[Part 4](https://protocols.opentrons.com/protocol/0961d2-part4)


This protocol performs the first half of Step 3 (SB Pooling). During this protocol, 1-4 SBP96 plates from [Part 2](https://protocols.opentrons.com/protocol/0961d2-part2) can be loaded on to the deck of the OT-2. Every six columns from the SBP96 plates are pooled into one column of a clean, 96-well plate (columns 1-6 of SBP96 plate 1 are pooled into column 1 of clean plate; columns 7-12 of SBP96 plate 1 are pooled into column 2 of clean plate; columns 1-6 of SBP96 plate 2 are pooled into column 3 of clean plate, etc).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [plexWell LP 384 Kit](https://seqwell.com/products/plexwell-lp-384/)
- SBP96 Plate, containing samples from [Part 2](https://protocols.opentrons.com/protocol/0961d2-part2)
* [Opentrons P10 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Bio-Rad 96-Well Plate, 200µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate), clean and empty
* [Opentrons 10µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons 10µL Filter Tips

Slot 2: SBP96 Plate, containing samples

Slot 3: Bio-Rad Plate, clean and empty

Slot 4: Opentrons 10µL Filter Tips (optional)

Slot 5: SBP96 Plate, containing samples (optional)

Slot 6: *Empty*

Slot 7: Opentrons 10µL Filter Tips (optional)

Slot 8: SBP96 Plate, containing samples (optional)

Slot 9: *Empty*

Slot 10: Opentrons 10µL Filter Tips (optional)

Slot 11: SBP96 Plate, containing samples (optional)


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
0961d2-part3
