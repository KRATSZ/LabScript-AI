# DNA dilution using .csv file

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates dilution of DNA in wells in a plate (Plate 1) with TE in a second plate (Plate2). The protocol does this using an input .csv file with 3 columns: plate1 (for the well location to transfer), DNA (for volume of DNA to transfer), and TE Buffer (for volume of TE to transfer). TE is loaded from a trough initially into Plate 2, and then the DNA is loaded into Plate 2 from Plate 1.

The protocol can transfer at 1-20ul of DNA and 20-200ul of TE into Plate 2. 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [NEST 1 Well Reservoir 195 mL](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load TE into a single well trough on deck position 8. The amount of TE required will be slightly higher than the amount needed for dilution of DNA.
2. Load input Plate 1 into deck position 6, and an empty output Plate 2 into deck position 9.
3. Load p300 tips into deck position 7 and p20 tips into deck position 5.
4. Run the protocol!

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
30174a
