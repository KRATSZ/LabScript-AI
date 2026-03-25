# Nanomaterial toxicity assay 

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA

## Description
This is a protocol to run a nanomaterial toxicity test. The nanomaterials get added at different concentrations to a plate, are dried, and then cells are exposed to the dried nanosheets. 

There are 3 steps to this protocol:

1. Nanomaterials are added at different concentrations to a 384 well plate. (drying done out of OT2 to make nanosheets)
2. Nanosheets are washed with PBS and bacteria are added to the sheets. (5hrs at 37.5c out of OT2)
3. Bacteria are removed from the nanosheets and the nanosheets are washed with PBS. (Plate ready for imaging on the Opera Phenix) 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [NEST 1 Well Reservoir 195 mL](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 96 Deepwell Plate 2mL](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [OMNI Pre-filled 2 mL 96 deep well plates with 1.4 mm Ceramic beads](https://www.omni-inc.com/consumables/well-plates/2-pack-96-well-plate-1-4mm-ceramic.html)
* [MagMAX Plant DNA Isolation Kit](https://www.thermofisher.com/order/catalog/product/A32549#/A32549)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
<<<<<<< HEAD:protocols/43163c/README.md
1. (Step 1) Load all labware. On the 12 well reagent reservoir, load 1:10 GO on column 1, 1:100 GO on column 2, MoS2 on column 3, 1:10 MoS2 on column 4, MoSe2 on column 5, and 1:10 MoSe2 on column 6. After running, remove experimental 384 well plate and dry at 60c.
2. (Step 2) Load all labware, including live bacteria. After PBS washes and adding of the bacteria, incubate at 37.5 for 5 hours.
3. (Step 3) Load all labware. After PBS washes, plate is ready for imaging.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
43163c
