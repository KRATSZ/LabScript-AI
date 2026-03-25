# MagMAX Viral/Pathogen Nucleic Acid Isolation Kit wash steps

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* MagMAX Nucleic Acid Isolation Kit

## Description
This protocol automates the wash steps of the MagMAX Viral/Pathogen Nucleic Acid Isolation Kit. As inputs, it requires a deep well plate with sample beads, a single well trough of 80% ethanol, a single well trough of wash buffer, a single well trash, and an output 96 well plate.

There are 2 pauses during the protocol that require human intervention - to drain the liquid trash + to replace tip racks + to add elution buffer, and to add the deep well plate to a 65c incubator for 10 minutes.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [NEST 1 Well Reservoir 195 mL](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Deepwell Plate 2mL](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [MagMAX Viral/Pathogen Nucleic Acid Isolation Kit](https://www.thermofisher.com/order/catalog/product/A42352?SID=srch-hj-A42352#/A42352?SID=srch-hj-A42352)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load reagents to deck. At least 50ml of wash buffer are required per run, and at least 75ml of 80% ethanol.
2. After second ethanol wash step, drain liquid trash, replace tip boxes, and replace 80% ethanol with at least 5-6ml of elution buffer.
3. After samples are resuspended in elution solution, move deep well plate to a 65c incubator for 10 minutes.
4. Move samples back to magdeck. Samples will be eluted into the 96 well plate on deck position 5.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1185d3
