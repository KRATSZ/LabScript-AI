# qPCR prep sample transfer 96 -> 384

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol builds a 384 well plate with from up to 14 columns from up to 2 96 well plates. It is a pythonization of [this protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2020-07-17/uo03r2t/Covid-19%2012%20columns%20.json), which only could not run a variable number of columns. This protocol is used for building qPCR plates.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [8-Channel Electronic Pipette (GEN2) P20](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/products/opentrons-20ul-filter-tips)
* [Hard-Shell 384-Well PCR Plates, thin wall, skirted, clear/white #HSP3805](https://www.bio-rad.com/en-us/sku/hsp3805-hard-shell-384-well-pcr-plates-thin-wall-skirted-clear-white?ID=hsp3805)
* [NEST 96 Deepwell Plate 2mL](http://www.cell-nest.com/page94?product_id=101&_l=en)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Download protocol with desired number of columns
2. Set plates onto robot, replace all tips with fresh tips, run

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
002af3
