# Normalization substituting a multi-channel pipette for a single-channel pipette

### Author
[Opentrons](https://opentrons.com/)

### Partner
[AstraZeneca](https://www.astrazeneca.com/)



## Categories
* Sample Prep
	* Normalization with a multi-channel pipette substituting for a single-channel pipette


## Description
![Normalization Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_example.png)

Concentration Normalization is a key component of many genomic and proteomic applications, such as NGS library preparation. With this protocol, you can easily normalize the concentrations of samples in a 96 or 384 microwell plate without worrying about missing a well or adding the wrong volume. Just upload your properly formatted CSV file (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol. This protocol is a modified version of our [Normalization Protocol](https://protocols.opentrons.com/protocol/normalization), that instead uses a multi-channel pipette as single channel pipette by picking up one tip at a time.

There is an optional [Part 2: Cherrypicking Protocol](https://protocols.opentrons.com/protocol/6d901d-2) to this protocol which performs cherrypicking using a multi-channel pipette in the same way.

**Note**: This protocol was updated for a change in our software stack and requires app 7.0 or greater.

Using the customization fields below, set up your protocol.
* `Volumes CSV`: Your input CSV specifying the normalization volumes. See the Setup section below for details.
* `P300 Multi Mount`: Select mount for P300 Multi-Channel Pipette
* `P20 Multi Mount`: Select mount for P20 Multi-Channel Pipette
* `Plate Type`: Select the model of microwell plate to normalize samples on.
* `Reservoir Type`: The type of the diluent reservoir. If you are selecting a multi-well reservoir you should place your diluent in well A1.
* `Use Filter Tips?`: Select whether your pipette will use regular or filter tips.
* `Tip Usage Strategy`: You can select whether your pipette will reuse the same tip throughout the entire normalization procedure or change tips after every diluent transfer.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.4.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Samples in a compatible plate (96-well or 384-well)](https://labware.opentrons.com/?category=wellPlate)
* [Automation-friendly reservoir](https://labware.opentrons.com/?category=reservoir)
* Diluent

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---

![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**CSV Format**

Your file must be saved as a comma separated value (.csv) file type. Your CSV must contain values corresponding to volumes in microliters (μL). It should be formatted in “landscape” orientation, with the value corresponding to well A1 in the upper left-hand corner of the value list.

![Normalization CSV](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_csv.png)

In this example, 40μL will be added to A1, 41μL will be added to well B1, etc.

If you would like to follow our template, you can make a copy of [this spreadsheet](https://opentrons-protocol-library-website.s3.amazonaws.com/Technical+Notes/normalization/Opentrons+Normalization+Template.xlsx), fill out your values, and export as CSV from there.

*Note about CSV*: All values corresponding to wells in the CSV must have a value (zero (0) is a valid value and nothing will be transferred to the corresponding well(s)). Additionally, the CSV can be formatted in "portrait" orientation. In portrait orientation, the bottom left corner is treated as A1 and the top right corner would correspond to the furthest well from A1 (H12 in a 96-well plate).


### Robot
* [OT-2](https://opentrons.com/ot-2)

### Deck Setup
Example deck setup starting state, note that the cherry picking plate in slot 8 is a place-holder and is used in the optional 2nd part of the protocol. The different colors on the normalization plate wells illustrates samples with different concentrations before being normalized.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d901d/example_deck.jpg)
* Well A1 on the reservoir on slot 9: Diluent, e.g. water or buffer.

### Protocol Steps
1. The protocol reads the input .csv file and loads the selected labware and pipettes.
2. The protocol uses the loaded multi-channel pipette as a single channel pipette to transfer the volume of diluent specified in the csv cell to the given well on the normalization plate. The multi-channel pipette picks up the bottom-most tip in a given tiprack column in order to only pick up one tip at a time. Depending on the `tip usage strategy` the pipette reuses the same tip for every step or it discards the used tip and picks up a new one for every transfer.
3. The protocol repeats step 2 for each well on the plate until each well on the plate has been normalized.

## Process

1. Create your CSV file according to our instructions.
2. Upload your CSV and select all desired settings according to the “Setup” section above to customize your protocol run.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
5. Make sure to add reagents to your labware before placing it on the deck! Your diluent should be in your reservoir, and the samples you’re normalizing should be in your plate.

### Additional Notes

If you’d like to request a protocol supporting multiple plates or require any other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
6d901d
