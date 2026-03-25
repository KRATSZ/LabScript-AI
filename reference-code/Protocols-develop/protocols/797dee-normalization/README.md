# Normalization with 50ml tubes

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
![Normalization Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_example.png)

Concentration normalization is a key component of many genomic and proteomic applications, such as NGS library prep. With this protocol, you can easily normalize the concentrations of samples in a 96 or 384 microwell plate without worrying about missing a well or adding the wrong volume. Just upload your properly formatted CSV file (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Samples in a compatible plate (96-well or 384-well)](https://labware.opentrons.com/?category=wellPlate)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* Diluent

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**CSV Format**

Your file must be saved as a comma separated value (.csv) file type. Your CSV must contain values corresponding to volumes in microliters (μL). It should be formatted in “landscape” orientation, with the value corresponding to well A1 in the upper left-hand corner of the value list.

![Normalization CSV](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_csv.png)

In this example, 40μL will be added to A1, 41μL will be added to well B1, and so on.

If you’d like to follow our template, you can make a copy of [this spreadsheet](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/797dee-normalization/Opentrons+Normalization+Template.xlsx), fill out your values, and export as CSV from there.

*Note about CSV*: All values corresponding to wells in the CSV must have a value (zero (0) is a valid value and nothing will be transferred to the corresponding well(s)). Additionally, the CSV can be formatted in "portrait" orientation. In portrait orientation, the bottom left corner is treated as A1 and the top right corner would correspond to the furthest well from A1 (H12 in a 96-well plate).

Using the customization fields below, set up your protocol.
* Volumes CSV: Upload the CSV (.csv) containing your diluent volumes.
* Pipette Model: Select which pipette you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right)
* Plate Type: Select which (destination) plate you will use for this protocol.
* Volume in 50ml: What is the starting volume of in your 50mL tube of diluent?
* Filter Tips: Specify whether you want to use filter tips.
* Tip Usage Strategy: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.



### Robot
* [OT-2](https://opentrons.com/ot-2)


## Process

1. Create your CSV file according to our instructions.
2. Upload your CSV and select all desired settings according to the “Setup” section above to customize your protocol run.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
5. Make sure to add reagents to your labware before placing it on the deck! Your diluent should be in a 50ml tube in the A3 spot (upper left) of your tube rack, and the samples you’re normalizing should be in your plate.


### Additional Notes

If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/apiv2index.html). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
normalization
