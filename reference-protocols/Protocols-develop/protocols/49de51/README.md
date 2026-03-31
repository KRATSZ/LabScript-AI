# ThermoFisher MagMAX Plant DNA Isolation Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA

## Description
This protocol automates the ThermoFischer MagMAX Plant DNA Isolation Kit on up to 96 samples in 1 96 well plate. This protocol is broken into 5 different phases that require human intervention. Throughout the protocol, tips are replaced as needed by the user. Please replace all tip boxes when requested.

Each reagent mL value in the Process section was calculated using the raw minimum amount of reagenet + 10%. More or less of each may be required.

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
1. Load reagents reservoir. In the 12 column reagent reservoir on deck position 3, add 7.392ml lysis buffer B to the 1st column, 2.112ml RNAse A to the 2nd column, 13.728ml precipitation solution to the 3rd column, 2.640ml sample prep beads to the 4th column, and 15ml elution buffer in the 5th column. 
2. Load 52.8ml lysis buffer A to a single column reservoir on deck position 5 and 42.24ml ethanol to a single column reservoir on deck position 2. Later in the run, Lysis buffer A will be replaced by 42.24ml wash buffer 1, and ethanol will be replaced by 84.48ml wash buffer 2. The program will prompt for these replacement steps.
3. Load all other labwares as requested by the labware setup on the robot.
4. Press Run on robot
5. After initial lysis, remove plate from deck and homogenize the samples, then return the plate to the temperature module on the robot.
6. After precipitation solution is added, incubate the plate on ice for 5 minutes, then return plate to the deck. Make sure there is a fresh deep well plate on the magnetic module. Replace lysis buffer A with wash buffer 1.
7. After the initial wash step, replace ethanol with wash buffer 2.
8. After the additional wash steps, vortex the plate from the magnetic module, and return it to the temperature module. Wait for 5 minutes.
9. After waiting, reurn the plate from the temperature module to the magdeck. Replace the original plate at position 6 with a new skirted PCR plate. 

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
49de51
