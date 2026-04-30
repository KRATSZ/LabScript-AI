# Cherrypicking

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Sample Prep
	* Cherrypicking

## Description
![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Cherrypicking, or hit-picking, is a key component of many workflows from high-throughput screening to microbial transfections. With this protocol, you can easily select specific wells in any labware without worrying about missing or selecting the wrong well. Just upload your properly formatted CSV file (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol.

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

Labware will be loaded automatically by specifying the labware loadname and labware slot in the .csv file. All available empty slots will be filled with the necessary [tipracks](https://shop.opentrons.com/collections/opentrons-tips), and the user will be prompted to refill the tipracks if all are emptied in the middle of the protocol.

**CSV Format**

Your cherrypicking transfers must be saved as a comma separated value (.csv) file type. Your CSV must contain values corresponding to volumes in microliters (μL). Note that the header line (first row of the .csv file) should also be included!

Here's an example of how a short cherrypicking protocol should be properly formatted:

```
New Tip,Source Labware,Source Slot,Source Well,Source Aspiration Height Above Bottom (in mm),Dest Labware,Dest Slot,Dest Well,Dest Dispense Height Above Bottom (in mm),Volume (in ul)
yes,agilent_1_reservoir_290ml,1,A1,1,nest_96_wellplate_100ul_pcr_full_skirt,4,A11,2,1
,nest_12_reservoir_15ml,2,A1,1,corning_384_wellplate_112ul_flat,5,B11,2,3
yes,nest_1_reservoir_195ml,3,A1,1,corning_384_wellplate_112ul_flat,5,A12,2,7
```

In the above example, 1μL will be transferred from 1mm above the bottom of well A1 in an Agilent 1-well 290ml reservoir (slot 1) to well A11 in the destination NEST 96-well plate 100µl (slot 4) with a new tip. After this, 3μL will be transferred from 1mm above the bottom of well A1 in a NEST 12-well 15ml reservoir (slot 2) to well A5 in the destination NEST 96-well plate 100µl (slot 5) with the same tip. Last, 7μL will be transferred from 1mm above the bottom of well A1 in a NEST 1-well 195ml reservoir (slot 3) to well H12 in the destination NEST 96-well plate 100µl (slot 5) with a new tip.

If you’d like to follow our template, you can make a copy of [this spreadsheet](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/274d2a/ex.csv), fill out your values, and export as CSV for use with this protocol.

Using the customizations fields, below set up your protocol.
* Transfer .csv File: Upload the .csv file containing your well locations, volumes, and source plate (optional).
* Pipette Model: Select which pipette you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right)
* Tip Type: Specify whether you want to use filter tips.
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
274d2a
