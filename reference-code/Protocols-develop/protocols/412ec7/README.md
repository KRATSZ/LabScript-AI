# Serial Dilution for Eskil

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Serial Dilution
	* Optional Temperature Module Serial Dilution

## Description
With this protocol, you can do the requested serial dilution with or without a temperature module under the 96-well plate using an 8-channel P300 pipette. The dilution factor and choice of plate are also modifiable.

![serial dilution](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/customizable-serial-dilution/Customizable+Serial+Dilution+Illustration+LATEST+VERSION.jpg)

***Example Setup***

This protocol uses the inputs you define for "***Dilution Factor***" and "***Total Mixing Volume***" to automatically infer the necessary transfer volume for each dilution across your plate. For a 1 in 3 dilution series across an entire plate, as seen above:

-- Start with your samples/reagents in Column 1 of your plate. In this example, you would pre-add 150 uL of concentrated sample to the first column of your 96-well plate.

-- Define a ***Total Mixing Volume*** of 150uL, a ***Dilution Factor*** of 3, and set ***Number of Dilutions*** = 11.

-- Your OT-2 will add 100uL of diluent to each empty well in your plate. Then it will transfer 50uL from Column 1 between each well/column in the plate.

-- "***Total mixing volume***" = transfer volume + diluent volume.

-- "Tip Use Strategy" will set whether a new tip will be used for every transfer or the same tip reused

-- "Blank in Well Plate" will set whether a blank will be added to column 12

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/customizable-serial-dilution/materials.png)

-- [Opentrons OT-2](http://opentrons.com/ot-2)

-- [Opentrons OT-2 Run App (Version 4.7 or later)](http://opentrons.com/ot-app)

-- [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips-racks-9-600-tips) for selected Opentrons Pipette

-- [12-Row, Automation-Friendly Trough](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)

-- 96-Well Plate, Bio-Rad or NEST full skirted plates or equivalent aluminum block plates

-- Diluent (Pre-loaded in row 1 of trough)

-- Samples/Standards (Pre-loaded in Column 1 of a standard 96-well plate)

### Deck Setup

DECK SETUP IMAGE HERE

Slot 1: Nest 12 Well 15ml Reservoir

Slot 2 and 3: Opentrons 300ul Tiprack

Slot 4: 96 Well Plate, with or without temperature module (specified in parameters)

### Protocol Steps
1. Load labware as specified in protocol
2. Load original, undiluted samples in column 1 in slot 4
3. Diluent is added to specified number of columns starting at 2, continuing on until specified number of wells are prepped
4. Specified amount of undiluted sample is transfered from column 1 to column 2. Column 2 is then mixed 5 times using all but 5ul of the resultant volume.
5. 3 and 4 are repeated for number of dilutions e.g. column 2 is then added to 3 and mixed, 3 added to 4 and mixed, etc.
6. If requested, a blank is added to column 12 consisting of only diluent (max number of dilutions with blank is 10)


### Process
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
412ec7
