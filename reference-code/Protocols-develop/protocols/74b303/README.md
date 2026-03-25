# Four Plate Normalization and Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Normalization
	* Normalization and Pooling

## Description
This protocol automates the normalization of samples provided on four 96 well PCR plates. Normalization of achieved by dispensing custom volumes (specified in the uploaded csv file) of water to each well of the initial pcr plate with the single channel p20, followed by mixing, and then pooling of 5 ul sample aliquots into a separate tube (one for each plate) located in the 24 tube rack.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [csv file](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-02-20/9l23lox/4Plate_Norm_ex.csv)
* [opentrons_24_tuberack_nest_2ml_screwcap](https://labware.opentrons.com/opentrons_24_tuberack_nest_2ml_screwcap?category=tubeRack)
* [nest_12_reservoir_15ml](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Transfer appropriate amount (from .csv) water from the NEST 12-well reservoir 15 ml to 96-well PCR Plate 1 (use same tip - single channel 20ul GEN2/right mount).
2. Repeat for Plate 2, Plate 3 and Plate 4.
3. Pool using same tip, transfer 5ul from each well in 96-well PCR Plate 1, to A1 of Opentrons 24 Tube Rack with NEST 2 mL Snapcap (include 3x mixing step before adding to 2 ml tube).
4. Repeat for all plates, with Plate 2 pooled into B1 of tube rack, Plate 3 pooled into C1 and Plate 4 pooled into D1.
