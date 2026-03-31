# Zymo Extraction Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Extraction


## Description
This protocol performs a [Zymo](https://www.zymoresearch.com/) extraction. The protocol splits elutes (up to 48) six columns apart (for ex, wells `A1` and `A7`).


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P50 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons Tube Rack, 24-well](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Opentrons Tube Rack, 6-Well](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [NEST 1-Channel Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* Zymo Elution Plate
* Zymo Block Plate
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Zymo Elution Plate, clean and empty

Slot 2: [Opentrons Tube Rack, 24-well](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 2mL Tubes
* A1: Proteinase K
* A2: Magbeads
* B1: DNase/RNase-Free Water
* B2: DNase/RNase-Free Water

Slot 3: [Opentrons Tube Rack, 6-well](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 50mL Falcon Tubes
* A1: Pathogen DNA/RNA Buffer
* A2: Wash Buffer 1
* B2: Wash Buffer 2
* A3: Ethanol
* B3: Ethanol

Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with 200µL Sample in Zymo Block Plate

Slot 5: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 6: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 7: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 8: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 9: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 10: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 11: [NEST 1-Channel Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir) (for liquid waste)




**Using the customizations fields, below set up your protocol.**
* **Number of Samples**: Specify the number of samples (1-48) you'd like to run.
* **P50 Single Mount**: Select which mount (left or right) the P50 Single is attached to.
* **P1000 Single Mount**: Select which mount (left or right) the P1000 Single is attached to.
* **MagDeck Incubation Time (mins)**: Specify how long (in minutes) the MagDeck should be engaged to create pellet, before removing supernatant.
* **Water Volume (for elution)**: Specify how much DNase/RNase-Free Water (in microliters) to add to each sample. This elution volume will then be split in two different wells in equal amounts.



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your zipped protocol bundle and unzip the file.
3. Upload your custom labware defintion into the [OT App](https://opentrons.com/ot-app) (only need to do this once).
4. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2) (only need to do this once).
7. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
343001
