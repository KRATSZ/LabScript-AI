# Custom Normalization & Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
![Normalization Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_example.png)

This protocol performs the normalization of samples by adjusting the concentration in Micronic 96 rack. Once normalized it will transfer nuclease-free water to the corresponding wells in a PCR plate and then transfer samples to the corresponding wells in the PCR plate.

In this protocol, the ThermoFisher Nunc 96 Well Plate 2mL is used as the reservoir for water. You can define the volume of water placed in each well at the `Water Reservoir Volume per Well` parameter below. By default this value is 1500 uL. The robot will assume that each well it needs has a volume of 1500 uL and will keep track of how much water it has used per well before moving onto a new well. While, it keeps track of the volume per well, it will also adjust the height of how low the pipette moves to aspirate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 App](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**CSV Format**

Your file must be saved as a comma separated value (.csv) file type. Your CSV must contain values corresponding to volumes in microliters (μL). Below is an example of the format for the CSV.


```
Plate position,ng/ul,Volume,ng TOT,ul Final Dil,ul Water
A1,19.9,15,298.7,19.9,4.9
B1,22.4,15,335.5,22.4,7.4
C1,22.2,15,332.9,22.2,7.2
```

### Robot
* [OT-2](https://opentrons.com/ot-2)


## Process

1. Create your CSV file based on the format provided.
2. Upload your CSV, choose your pipette mount positions and enter the final concentration for normalization.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.


### Additional Notes

If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
08aeaa
