# Mastermix Creation and Sample Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the creation of a mastermix (containing OptiMEM, DNA samples, and Viafect) and then dispenses this mastermix in triplicate. Using a simple CSV and a couple key parameters, this protocol can be easily adjusted for diifferent scenarios.</br>
</br>
The protocol begins by adding 5.3µL of OptiMEM to the number of wells as defined by the user (the last well can receive more). After this, 4.4µL of DNA will be added to the wells per the CSV, transferring from sample tubes in deck slot 4 to the mastermix tubes in deck slot 5 (with OptiMEM). The OT-2 will then add 1.3µL of Viafect to the mastermix wells and pause until the user is ready to resume. After resuming, the OT-2 will transfer 10µL of the mastermix, in triplicate, to a 96-well plate in deck slot 6.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Corning 96-Well Plate, 360µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [1.5mL Microcentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* PCR Strips, 200µL



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


**Deck Setup**</br>
</br>
Slot 1: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)</br>
Slot 2: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)</br>
Slot 3: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips)</br>
Slot 4: [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with PCR Strips containing samples/stock</br>
Slot 5: [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with empty PCR Strips on the left for mastermix creation (columns 1-4) and a PCR Strip containing Viafect (column 12)</br>
Slot 6: [Corning 96-Well Plate, 360µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)</br>
Slot 7: [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with a [1.5mL Microcentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) containing OptiMEM in D6</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Transfer CSV**: Upload a CSV that will dictate the transfer of DNA from deck slot 4 to deck slot 5 (see below for more detail)
* **Number of Mastermix**: Specify the number of mastermixes to be created (1-32).
* **Extra OptiMEM**: Specify whether the last mastermix tube should receive 31.7µL of OptiMEM or the standard 5.3µL
</br>
</br>
**CSV Layout**</br>
![CSV Template](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6b9ee3/6b9ee3_csv_img.png)
</br>
</br>
The CSV should consist of two columns with headers, **Source Well** and **Destination Well**. Using capital letters, you can simply put well locations and the pipette will transfer 4.4µL from the source well (in deck slot 4) to the destination well (in deck slot 5).

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Upload your CSV and select parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6b9ee3
