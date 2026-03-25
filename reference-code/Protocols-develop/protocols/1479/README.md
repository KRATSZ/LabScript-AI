# DNA Concentration Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description
With this protocol, your robot can normalize concentration of DNA samples from 2 mL Eppendorf tubes in PCR strips. Volumes of DNA and buffer for each normalization will be provided by the user as a CSV file. See Additional Notes for more details.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.20.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P10 and P50 Single-Channel Pipette (GEN1)](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [4-in-1 Tube Rack Set with 4x6 insert for 2ml Eppendorf tubes](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* standard PCR strips

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

CSV layout (keep the headers)

```
Source tube rack,Source tube well,Destination well,Vol. of DNA  (?gL),Vol. of diluent  (?gL)
Slot 3,A1,A1,7,8
Slot 3,B1,B1,6.4,8.6
Slot 3,C1,C1,9.2,5.8
Slot 3,D1,D1,6,9
```

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Create your CSV file according to our instructions.
2. Upload your CSV and select all desired settings according to the “Setup” section above to customize your protocol run.
3. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
4. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
5. Make sure to add samples to your labware before placing them on the deck! Your source plate should contain the samples you want to pick.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/apiv2index.html). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
1479
