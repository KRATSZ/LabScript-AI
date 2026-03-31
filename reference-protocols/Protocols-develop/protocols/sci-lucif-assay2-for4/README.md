# Luciferase Reporter Assay for NF-kB Activation (up to 4 plates) - Protocol 2: Transfection of Luciferase Reporter Construct


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
The protocol performs liquid handling to conduct transient DNA transfection to develop reporter cells in a 96-well setting for luciferase reporter assay.

The luciferase reporter assay is used to investigate the regulation of expression of a gene of interest. This method relies on reporter cells created by stable or transient transfection of a promoter-driven, luciferase-expressing DNA. The bioluminescence proportional to luciferase expression can be quantified to assess the functional connection between the expression of the target gene which is controlled by this promoter, and the factor to be studied which may exhibit a regulatory effect on the cell behaviors at the transcription level. In this particular example, HeLa cells are stably or transiently transfected with an NF-kB promoter-driven, luciferase reporter construct, treated with an NF-kB activator phorbol 12-myristate 13-acetate (PMA), and activation of NF-kB assessed by measuring the luciferase enzymatic activity.

Transfection reagent preparation:
To make the reagent for 100 reactions (sufficient for a 96-well plate), dilute 10 µL  (0.1 µL per reaction) of NanoLuc Reporter Vector with NF-κB Response Element (Promega, Madison, WI, USA) in 1 mL (10 µL per reaction) serum free DMEM (Thermo Fisher Scientific, Waltham, MA, USA) and then add 30 µL  (0.3 µL per reaction) of FuGENE HD Transfection Reagent (Promega, Madison, WI, USA). After 10-minute incubation at room temperature, the transfection reagent/DNA mixture is brought up to 2 mL by adding serum free DMEM and then distributed to fill a column (250 µL per well, 8 well per column) of a NEST 96 Deep Well Plate.


### Labware
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons HEPA Filter Module](https://opentrons.com/products/modules/hepa/)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif-assay2-for4/deck.png)


### Reagent Setup

1. A NEST 96 Deep Well Plate 2mL filled with transfection master mix in Column 1 to Column 4 (for up to four 96-well plates) loaded on Slot 6 (MASTER MIX)
2. Reporter cell culture (up to four Corning 96 Well Plate 360 µL Flat) loaded on Slot 2, 5, 8 and 11
3. An Opentrons 96 Tip Rack 300 µL loaded on Slot 8


### Protocol Steps
1. Transfer transfection reagent/DNA mixture from Slot 6 (MASTER MIX, Column 1) to cell culture on Slot 2 (20 µL per well)
2. Transfer transfection reagent/DNA mixture from Slot 6 (MASTER MIX, Column 2) to cell culture on Slot 5 (20 µL per well)
3. Transfer transfection reagent/DNA mixture from Slot 6 (MASTER MIX, Column 3) to cell culture on Slot 8 (20 µL per well)
4. Transfer transfection reagent/DNA mixture from Slot 6 (MASTER MIX, Column 4) to cell culture on Slot 11 (20 µL per well)
5. Continue cell culture incubation (off deck)


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
sci-lucif-assay2-for4
