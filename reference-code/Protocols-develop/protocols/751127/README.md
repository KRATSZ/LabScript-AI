# Cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description

This is a flexible protocol to accommodate .csv file-specified coordinates. You can upload your coordinates for 2 sources and up to 10 locations specified in the .csv template [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/751127/CSV+Template+-+Sheet1.csv), and upload your edited template below at the parameter `Transfer .csv File`. The template has some pre-defined values, but you will likely need to modify these values to suit your specific labware and workflow.

Note that the coordinates are defined in millimeters from the bottom left-most corner of the Opentrons deck slot 1.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons P20 GEN2 Single-Channel Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 20µl Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Create your CSV file according to our instructions.
2. Upload your CSV and select all desired settings according to the “Setup” section above to customize your protocol run.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
751127
