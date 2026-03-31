# Cherrypicking (Simple)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking


## Description
![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Cherrypicking, or hit-picking, is a key component of many workflows from high-throughput screening to microbial transfections. With this protocol, you can easily select specific wells in a 96 or 384 microwell plate without worrying about missing or selecting the wrong well. Just upload your properly formatted CSV file (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Microplates (96-well or 384-well)](https://labware.opentrons.com/?category=wellPlate)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

[Tipracks](https://shop.opentrons.com/collections/opentrons-tips) should be loaded in **Slot 1** (if using more than 96 tips, Slots 4, 7, and 10 can be loaded as well).

The Source Plate should be loaded in **Slot 2**. If using multiple Source Plates, Source Plates 1, 2, 3, and 4 should be loaded into **Slot 2**, **Slot 5**, **Slot 8**, and **Slot 11**, respectively.
*Note*: If using multiple Source Plates, you must specify the Source Plate in the third column of the CSV (see below for examples)

The Destination Plate should be loaded in **Slot 3**.
*Note*: The Destination Plate will receive each cherrypicking transfer sequentially, filling up the plate in well A1, then B1, etc.

**CSV Format**

Your cherrypicking transfers must be saved as a comma separated value (.csv) file type. Your CSV must contain values corresponding to volumes in microliters (μL).

![Cherrypicking CSV ex1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cp_csv_ex1.png)

In the first example, 40μL will be removed from well A3 in your source plate, and placed in well A1 in your destination plate. 36μL will be removed from well D4 in your source plate, and placed in well B1 in your destination plate.

![Cherrypicking CSV ex2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cp_csv_ex2.png)

In the second example, 100μL will be transferred from well E5 in "Plate 1" (slot 2) to well A1 in the destination plate (slot 3). After this, 100μL will be transferred from well G10 in "Plate 3" (slot 8) to well B1 in the destination plate (slot 3).

If you’d like to follow our template, you can make a copy of [this spreadsheet](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/cherrypicking_simple/Opentrons+Cherrypicking+Simple+Example+Template.xlsx), fill out your values, and export as CSV for use with this protocol.

Using the customizations fields, below set up your protocol.
* Volumes CSV: Upload the .csv file containing your well locations, volumes, and source plate (optional).
* Pipette Model: Select which pipette you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right)
* Source Plate Type: Select which (source) plate you will pick samples from.
* Destination Plate Type: Select which (destination) plate you will dispense into.
* Filter Tips: Specify whether you want to use filter tips.
* Tip Usage Strategy: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Create your CSV file according to our instructions.
2. Upload your CSV and select all desired settings according to the “Setup” section above to customize your protocol run.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
5. Make sure to add samples to your labware before placing them on the deck! Your source plate should contain the samples you want to pick.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
cherrypicking_simple
