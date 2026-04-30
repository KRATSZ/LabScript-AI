# Generic Sample Plating Protocol (Station A)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* Sample Plating


## Description
This protocol automates sample plating from collection tubes to a 96-well plate. After sample plating (Station A), the plate containing samples can be used on Station B for RNA extraction as outlined in our [article on automating Covid-19 testing](https://blog.opentrons.com/how-to-use-opentrons-to-test-for-covid-19/).</br>
</br>
Using a [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will transfer the user-specified volume from sample tubes placed in the [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) into a 96-well plate. Users can specify which pipette, the type of source tube, the type of destination plate, the number of samples to transfer, and the volume of each sample being transferred.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* 96-Well Plate
* Sample Tubes



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

The [Opentrons tiprack](https://shop.opentrons.com/collections/opentrons-tips) should be placed in slot 3 and the 96-well plate should be placed in slot 2.</br>

With this protocol, the [Opentrons tube rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with samples will be accessed in the following order: slot 1, 4, 7, 10, 5, 8, 11 -- see below for examples.</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify the number of samples to run (1-96)
* **Volume of Samples (in µL)**: Specify the volume to be transferred from sample tubes to destination plate (this volume should fall in the range of the selected pipette)
* **Destination Plate Labware**: Specify whether to use the [NEST Deepwell Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) or the [NEST PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) as the destination plate
* **Source Tube Labware**: Specify whether to use the Opentrons Tubebrack (24) with [2mL](https://labware.opentrons.com/opentrons_24_tuberack_nest_2ml_screwcap?category=tubeRack), [1.5mL](https://labware.opentrons.com/opentrons_24_tuberack_nest_1.5ml_screwcap?category=tubeRack), or [0.5mL](https://labware.opentrons.com/opentrons_24_tuberack_nest_0.5ml_screwcap?category=tubeRack) tubes or the Opentrons Tuberack (15) with [15mL](https://labware.opentrons.com/opentrons_15_tuberack_falcon_15ml_conical?category=tubeRack) conical tubes.
* **Pipette Type**: Specify which pipette (p300/p1000 GEN1/GEN2) to use (should be mounted on the right gantry)
</br>
</br>
**Example layout: 15 samples with 2mL tubes**</br>
![15 samples with 2mL tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_A/stationA_2_15.png)
</br>
</br>
**Example layout: 15 samples with 15mL tubes**</br>
![15 samples with 15mL tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_A/stationA_15_15.png)
</br>
</br>
**Example layout: 96 samples with 2mL tubes**</br>
![96 samples with 2mL tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_A/stationA_2_96.png)
</br>
</br>
**Example layout: 96 samples with 15mL tubes**</br>
![96 samples with 15mL tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/station_A/stationA_15_96.png)
</br>
</br>


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
generic_station_A
