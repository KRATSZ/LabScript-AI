# PCR setup using a CSV File

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates PCR setups using a CSV file. Slots 2, 5, 8, and 11 are reserved for input tube racks. Slot 6 is reserved for a 384 well PCR plate and slot 9 is reserved for a 96 well PCR plate. The rest of the slots are reserved for tips.</br>
</br>
**Update (Jan 13, 2021)**: A fix was added that was preventing use of slots 5, 8, and 11.

Customize the PCR setup CSV and upload it to get a custom protocol. Template CSV can be found [here](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/3fb582/PCR+Setup+Template+-+Sheet1.csv).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons P20-single channel electronic pipettes (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/products/tube-rack-set-1)
* 384 or 96 well PCR plate

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Load reagents and labware into required slots.
2. Run the protocol.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3fb582
