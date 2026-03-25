# CerTest VIASURE SARS-CoV-2 Real Time PCR Detection transfer step

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates the transfer of rehydration buffer, samples, positive control, and negative control from the CerTest VIASURE SARS-CoV-2 Real Time PCR Detection kit into a PCR plate. It requires a 96 deep well plate of samples (1-94), the positive and negative control tubes in a tube rack, and a new PCR plate. This protocol uses exactly 2 tip racks and takes advantage of manually programmed multichannel transfers so that it only requires a p20 multichannel pipette. 

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-multi channel electronic pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5978988707869)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [NEST 1 Well Reservoir 195 mL](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [VIASURE SARS-CoV-2 Real Time PCR Detection Kit](https://www.certest.es/viasure/)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load TE into a single well trough on deck position 8. The amount of TE required will be slightly higher than the amount needed for dilution of DNA.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
33b12a
