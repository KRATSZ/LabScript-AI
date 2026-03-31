# Standard Curve Dilutions with CSV File

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Serial Dilution

## Description
This protocol performs standard curve serial dilutions using data from a CSV file. It has the option to perform up to 2 standard curves per run and the ability to modify stock concentrations.

![Plate Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/543bf9/543bf9_plate_positions.png)
**Note**: The layout above depicts a full plate with 2 standard curves.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Setup**

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/543bf9/543bf9_deck_layout.png)

**CSV File Information**

The protocol will require a CSV file to be uploaded in order to properly function. Please use the following [Serial Dilutions Excel Spreadsheet Template (.XLSX Format)](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/543bf9/serial_dilutions_template.xlsx) to update your values. Once the values are updated click `Save As` and then save it in `.CSV` format. You can then upload that CSV to the protocol for your run.

**Protocol Steps**

1. Transfer 44.5 uL of Diluent into Int1 (Well A1).
2. Transfer 5.5 uL from Stock1 into Int1
3. Mix Int1 3 times, perform blow out, touch tip, then discard tip.

**Note**: This process will repeat as it iterates through the rows in the CSV and add diluent first, then the sample from the previous well or specified well.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
543bf9