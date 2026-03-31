# Sarah Daley Protocol (check mesoscale.com link)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA

## Description
This protocol automates {mesoscale kit} in 4 steps over 2 days. Those steps are:

1. (Day 1) Load blocking solution into test plates
2. (Day 2) Load standards and up to 10 sample columns from sample plates into 2 test plates
3. (Day 2) Load detection antibody into test plates
4. (Day 2) Load read buffer into test plates

The initial Day 1 step can be done with up to 9 test plates. The subsequent steps are done with 1 sample plate and then 2 test plates. To increase throughput, run the step again with a separate plate. 

Note all volumes requested in process are the amount required + 10%. You may need more or less given your particular robot and calibrations.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P300-multi channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [NEST 1 Well Reservoir 195 mL](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [{mesoscale kit{](https://example.com)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load necessary labware to positions.
2. For the first step, add 15.84ml of blocking solution per plate that you wish to fill to the single well trough. The "Test Plates" value is only required for this step.  
3. For the second step, add Xml of control 1 to well A1 and Xml of control 2 to well A2 of a 12 column trough. After this step, incubate and wash separately of Opentrons.
4. For the third step, add 2.640ml of the detection antibody to well A3 of a 12 column trough. After this step, incubate and wash separately of Opentrons.
5. For the fourth and final step, add 15.84ml of read buffer to a trough. This will be allocated to the test plates 

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1980cd
