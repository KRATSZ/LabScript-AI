# Ammonia ytrium dilution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol automates a request for a ammonia and ytrium dilution protocol. It uses 2 custom labwares, transferring 10ul of ammonia from a 50mL tube to a custom 99 well plate, then transferring 5ul of Ytrium from a custom 96 well plate on a shaker. This is repeated 96 times until all wells from the custom 96 well plate have been transferred.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [NEST 50mL centrifuge tubes](http://www.cell-nest.com/page94?product_id=110&_l=en)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load ammonia into a 50mL tube on the A1 slot on the tube rack. By default, this tube is full with 50mL of liquid. This variable is important so the pipette knows which height is safe to aspirate from.
2. Load the rest of the reagents onto the deck. Press go to run.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6aee6e
