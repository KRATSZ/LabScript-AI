# Mass spec sample prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA

## Description
This protocol was built for Mass Spec sample prep for IPM doctors. It transfers a variable volume of reagent between 24 well input plate(s) and 24 well output plate(s). There are 3 custom labwares that this protocol normally uses - a 7ml tube rack (24 slot),  a 1ml autosampler tube rack (24 slot), and a 24 MCT laser cut acrylic rack.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)


* [Opentrons P300-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [24 well plate](example.com)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load plates into proper deck slots. Sample plate at deck slot 2 will transfer into target plate at deck slot 5 and if there are more than 48 samples, sample plate at deck slot 3 will transfer into target plate at deck slot 6. 
2. Load tips at position 1. 
3. Run.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6d3eda
