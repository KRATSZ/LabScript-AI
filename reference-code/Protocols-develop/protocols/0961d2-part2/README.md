# plexWell LP384 Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* plexWell LP384


## Description
This protocol is part 2 of a 4-part protocol designed to accomplish the Sample-Barcoding Module of the [plexWell 384 Low Pass Library Preparation](https://seqwell.com/products/plexwell-lp-384/).


[Part 1](https://protocols.opentrons.com/protocol/0961d2-part1)
[Part 2](https://protocols.opentrons.com/protocol/0961d2-part2)
[Part 3](https://protocols.opentrons.com/protocol/0961d2-part3)
[Part 4](https://protocols.opentrons.com/protocol/0961d2-part4)


This protocol accomplishes Step 2 (SB Reaction Stop). During this protocol, 7.5µL of X Solution is added to each well of a 96-Well Plate (SBP96), containing samples from [Part 1](https://protocols.opentrons.com/protocol/0961d2-part1). With this protocol, you are given the option to use 1-4 plates for this step, for higher throughputs. The SBP96 plates should be loaded in the column containing slots 2, 5, 8, and 11 (sequentially). For each plate, a tip rack should be placed in the adjoining slot (slots 1, 4, 7, and 10).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [plexWell LP 384 Kit](https://seqwell.com/products/plexwell-lp-384/)
- SBP96 Plate, containing samples from [Part 1](https://protocols.opentrons.com/protocol/0961d2-part1)
- X Solution
* [Opentrons P10 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [NEST 12-Well Reservoir, 15mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* [Opentrons 10µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons 10µL Filter Tips

Slot 2: SBP96 Plate, containing samples

Slot 3: *Empty*

Slot 4: Opentrons 10µL Filter Tips (optional)

Slot 5: SBP96 Plate, containing samples (optional)

Slot 6: *Empty*

Slot 7: Opentrons 10µL Filter Tips (optional)

Slot 8: SBP96 Plate, containing samples (optional)

Slot 9: Nest 12-Well Reservoir
* Column 2: X Solution

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
0961d2-part2
