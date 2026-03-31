# Agriseq Library Prep Part 4 - Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* AgriSeq HTS Library Kit

## Description
This protocol is the fourth part of a four part series for performing NGS library prep with the [ThermoFisher Scientific AgriSeq kit](https://www.thermofisher.com/order/catalog/product/A34144#/A34144). Samples in plate are pooled into 60ul pools on a well plate. After which, 45ul from each pool is pooled into a single column.

**Note:** This protocol was updated on September 28th, 2022

Links:
* [Part 1: DNA Transfer](./7855ef)
* [Part 2: Pre-Ligation](./7855ef-part2)
* [Part 3: Barcoding](./7855ef-part3)
* [Part 4: Pooling](./7855ef-part4)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.7.0 or later)](https://opentrons.com/ot-app/)
* [P20 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P300 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)
* [ThermoFisher Scientific 96 Well Plate 200ul (4483352)](https://www.thermofisher.com/document-connect/document-connect.html?url=https%3A%2F%2Fassets.thermofisher.com%2FTFS-Assets%2FLSG%2Fbrochures%2FEnduraPlate_96Well.pdf&title=RW5naW5lZXJpbmcgRGlhZ3JhbTogTWljcm9BbXAmcmVnOyBFbmR1cmFQbGF0ZSZ0cmFkZTsgT3B0aWNhbCA5Ni13ZWxsIFJlYWN0aW9uIFBsYXRl)
* [BioRad Hard-shell 96-well PCR Plate Skirted](https://www.bio-rad.com/en-us/sku/hsp9631-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-blue-clear?ID=hsp9631)
* Custom 96 Well Endura Plate
* [Applied Biosystems 384-Well Plate](https://www.thermofisher.com/document-connect/document-connect.html?url=https://assets.thermofisher.com/TFS-Assets%2FLSG%2Fmanuals%2Fcms_042831.pdf)

**Note About Labware**
The ThermoFisher 96 well plate (model 4483352) is to be mounted on top of the BioRad Hard-shell plate, making one plate with a moniker of "Custom 96 Well Endura Plate".

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Using the customization fields below, set up your protocol.
* Number of Samples: Specify the number of samples to be processed in this run (max 384).
* P20 Mount: Specify which mount to load the P20 GEN2 pipette.
* Tip Disposal: Set the pipette to return tips to the tip rack immediately after use or in the trash bin first.


**Labware Setup**

Slots 1: Pool Plate (Custom 96 well Endura Plate)

Slot 5: Reaction Plate (Applied Biosystems 384-Well Plate)

Slot 7, 8, 9, 10: Opentrons 20ul Filter Tip Rack(s)

Slot 11: Opentrons 200ul Filter Tip Rack

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7855ef-part4
