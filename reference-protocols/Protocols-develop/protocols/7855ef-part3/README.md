# Agriseq Library Prep Part 3 - Barcoding

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* AgriSeq HTS Library Kit

## Description
This protocol is the third of a four part series for performing NGS library prep with the [ThermoFisher Scientific AgriSeq kit](https://www.thermofisher.com/order/catalog/product/A34144#/A34144). 1ul of IonCode Barcode Adapter is 1-1 transferred by well between the sample plate from Parts 1 & 2 and the Ion Code 96 well plate.

**Note**: This protocol was updated November 22nd, 2022

Links:
* [Part 1: DNA Transfer](./7855ef)
* [Part 2: Pre-Ligation](./7855ef-part2)
* [Part 3: Barcoding](./7855ef-part3)
* [Part 4: Pooling](./7855ef-part4)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [ThermoFisher Scientific 96 Well Plate 200ul (AB-0800)](https://www.thermofisher.com/document-connect/document-connect.html?url=https%3A%2F%2Fassets.thermofisher.com%2FTFS-Assets%2FLSG%2Fmanuals%2FMAN0014518_96well_pcr_plate_skirted_low_profile_qr.pdf&title=VGVjaG5pY2FsIERyYXdpbmcgLSBQQ1IgUGxhdGUsIDk2LXdlbGwsIExvdyBQcm9maWxlLCBTa2lydGVk)
* [ThermoFisher Scientific 96 Well Plate 200ul (4483352)](https://www.thermofisher.com/document-connect/document-connect.html?url=https%3A%2F%2Fassets.thermofisher.com%2FTFS-Assets%2FLSG%2Fbrochures%2FEnduraPlate_96Well.pdf&title=RW5naW5lZXJpbmcgRGlhZ3JhbTogTWljcm9BbXAmcmVnOyBFbmR1cmFQbGF0ZSZ0cmFkZTsgT3B0aWNhbCA5Ni13ZWxsIFJlYWN0aW9uIFBsYXRl)
* [BioRad Hard-shell 96-well PCR Plate Skirted](https://www.bio-rad.com/en-us/sku/hsp9631-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-blue-clear?ID=hsp9631)
* [Applied Biosystems 384 Well Plate](https://www.thermofisher.com/document-connect/document-connect.html?url=https://assets.thermofisher.com/TFS-Assets%2FLSG%2Fmanuals%2Fcms_042831.pdf)
* Custom 96 Well Endura Plate

**Note About Labware**
The ThermoFisher 96 well plate (model 4483352) is to be mounted on top of the BioRad Hard-shell plate, making one plate with a moniker of "Custom 96 Well Endura Plate".

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Using the customization fields below, set up your protocol.
* Number of Samples: Specify the number of samples to be processed in this run (max 384).
* P20 single GEN2 mount: Specify which mount to load the P20 single GEN2 pipette.


**Labware Setup**

Slots 1, 2, 3: Ion Code Barcode plates (Custom 96 well Endura plate)

Slot 5: 384 well plate

Slot 7: MMX Plate with Barcode Reaction Mix in Column 4

Slot 8, 9, 10, 11: Opentrons 20ul Tip Rack



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
7855ef-part3
