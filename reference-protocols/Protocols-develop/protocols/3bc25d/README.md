# Nanopore Rapid Barcoding Kit (SQK-RBK004)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Nanopore

## Description
This protocol automates the entire Oxford Nanopore sequencing kit SQK-RBK004 workflow. Input a variable number of samples (up to 12), and get out a pooled library. 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Rapid Barcoding Kit (SQK-RBK004)](https://store.nanoporetech.com/us/rapid-barcoding-kit.html)
* Fresh 70% Ethanol
* H2O
* [1.5mL centrifuge tubes](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load tubes into the temperature deck. Place RAP into tube A1 and AMPure beads (~150ul) into tube A2. In tubes B1 to C6 go your fragmentation mixes depending on the number of samples to be barcoded. The fragmentation mixes are placed in ascending order from B1 to B2 to B3 (etc). 
2. Load tubes into the tube rack. Place H2O (~500ul) into tube A1, fresh 70% ethanol (~600ul) into tube A2, and Tris-HCl with NaCl into tube A3. Place empty tubes in B2 and B3 - these will be used as liquid trash and as intermediate locations for samples. Also place an empty tube in C1 - this will be your output tube.
3. Load the rest of the deck as the protocol asks and press go. No intervention should be necessary, and you can take out your prepared library from tube C1 in the tube rack after the protocol finishes.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3bc25d
