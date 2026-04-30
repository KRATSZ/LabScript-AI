# Thermocycler from .csv

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Thermocycler
	* Thermocycler with CSV


## Description

This is a demo protocol, intended for using the [Opentrons Thermocycler Module](https://shop.opentrons.com/products/thermocycler-module) as a thermocycler. This protocol does not involve any liquid handling, so no pipettes are required to run this protocol. If you are interested in a custom protocol that uses the thermocycler to your lab's specific needs, you can request one from our Applications Engineering Team, using the [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/).


With this protocol, you can create steps for a a custom thermocycler profile.


Additionally, you can specify the lid temperature, sample volume per well, and a final hold temperature that will stay set until you're ready to move the samples.


For more information about the [Opentrons Thermocycler Module](https://shop.opentrons.com/products/thermocycler-module), please see the [Thermocycler Module white paper](https://opentrons.com/publications/Opentrons-Thermocycler-Module-White-Paper.pdf) or our [Thermocycler Module support article](https://support.opentrons.com/en/articles/3469797-thermocycler-module).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Thermocycler Module](https://shop.opentrons.com/products/thermocycler-module)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

The Thermocycler Module should be loaded into its default position in slots 7 and 10 (with some overhang in slots 8 and 11).


Before running the protocol with samples, use the button on top of the Thermocycler to open the lid (if closed) and place your sample plate into the Thermocycler. If needed, place an [Opentrons Thermocycler Seal](https://shop.opentrons.com/products/thermocycler-seals) on the lid. You do not need to close the lid before running the protocol.


**How to setup your Thermocycler profiles**
1. Download the template file [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/thermocycler/ex.csv)
2. Open the `.csv` file in a your spreadsheet editor of choice (Google Sheets, Excel, Numbers, etc.)
3. Export the edited file as `.csv`
4. Upload the new file in the field "profile .csv file" below.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Specify all desired settings according to the “Setup” section above to customize your protocol run.
2. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
3. If using samples, manually insert your sample plate into the Thermocycler on the OT-2 deck
4. Upload your protocol into the Opentrons App and proceed to run.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/OpentronsPythonAPIV2.pdf). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
thermocycler
