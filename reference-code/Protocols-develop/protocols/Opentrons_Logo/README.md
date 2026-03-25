# Opentrons Logo Protocol

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Getting Started
	* Opentrons Logo

## Description
This is a demo protocol that will help you to get more familiar with your new OT-2! All you need is some food dye, a 96-well plate, and a 12-row trough or tube rack with 1.5mL or 2mL tubes. Your robot will pipette the Opentrons logo into your plate and you'll be ready to go!

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [96-Well Microplate](https://labware.opentrons.com/?category=wellPlate)
* [12-Row Trough](https://labware.opentrons.com/?category=reservoir) or [Tube Rack with 1.5mL/2mL Tubes](https://labware.opentrons.com/?category=tubeRack)
* Water and Food Dye (Two Colors)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this demo protocol, you need a clean, empty 96-well plate (where the Opentrons logo will be created) and either a 12-row trough or 1.5mL/2mL tubes in a tube rack to store the water and food dye solution.

If using a 12-row trough, the two food dye solutions should be stored in column 1 and column 2. If using the tube rack, dye 1 should be stored in 'A1' & 'B1' and dye 2 should be stored in 'C1' & 'D1'.

Using the customization fields below, set up your protocol.
* Pipette Model: Select which pipette you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right)
* Destination Plate Type: Select which (destination) plate you will use for this protocol.
* Dye Labware Type: Select which (source) labware you will use for this protocol.


### Robot
* [OT-2](https://opentrons.com/ot-2)


### Time Estimate
* 2-5 minutes depending on pipette model chosen

### Reagents
* Food dye

## Process
1. Select all desired settings according to the “Setup” section above to customize your protocol run.
2. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
3. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
4. Make sure to add reagents to your labware before placing it on the deck! Your food dye solution should be in your labware and your destination plate should be empty.

### Additional Notes
If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
Demo Protocol 1
