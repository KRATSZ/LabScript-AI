# Luciferase Reporter Assay for NF-kB Activation - Protocol 2: Transfection of Luciferase Reporter Construct


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Broad Category
	* Specific Category


## Description
The protocol performs liquid handling to conduct transient DNA transfection to develop reporter cells in a 96-well setting for luciferase reporter assay. Multiple transfection master mixes can be used (e.g., different DNA vectors or various reagent concentrations are tested), and the user determines how many columns of cells (12 columns in a 96-well plate, 8 wells per column) are subjected to a master mix.

The luciferase reporter assay is used to investigate the regulation of expression of a gene of interest. This method relies on reporter cells created by stable or transient transfection of a promoter-driven, luciferase-expressing DNA. The bioluminescence proportional to luciferase expression can be quantified to assess the functional connection between the expression of the target gene which is controlled by this promoter, and the factor to be studied which may exhibit a regulatory effect on the cell behaviors at the transcription level. In this particular example, HeLa cells are stably or transiently transfected with an NF-kB promoter-driven, luciferase reporter construct, treated with an NF-kB activator phorbol 12-myristate 13-acetate (PMA), and activation of NF-kB assessed by measuring the luciferase enzymatic activity.

Transfection reagent preparation:
The table below lists examples of transfection master mix preparation. To make the reagent for 100 reactions (sufficient for a 96-well plate), dilute 10 uL (0.1 uL per reaction) of NanoLuc Reporter Vector with NF-κB Response Element (Promega, Madison, WI, USA) in 1 mL (10 uL per reaction) serum free DMEM (Thermo Fisher Scientific, Waltham, MA, USA) and then add 30 uL (0.3 uL per reaction) of FuGENE HD Transfection Reagent (Promega, Madison, WI, USA). After 10-minute incubation at room temperature, the total volume of this transfection reagent/DNA mixture is brought up to 2 mL by adding serum free DMEM. All master mixes are kept in 2 mL microcentrifuge tubes with snap cap, loaded on Opentrons 24 Tube Rack.


### Labware
* [Opentrons 24 Tube Rack with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif/Screen+Shot+2023-05-10+at+4.49.57+PM.png)
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif/pt2-2.png)


### Reagent Setup
1. An Opentrons 24 Tube Rack with NEST 2 mL Snapcap filled with master mixes loaded on Slot 3 (MASTER MIX)
2. Cell culture prepared in a Corning 96 Well Plate 360 µL Flat loaded on Slot 6 (WORKING PLATE)
3. An Opentrons 96 Tip Rack 300 µL loaded on Slot 8


### Protocol Steps
1. Transfer transfection reagent/DNA mixture from MASTER MIX to WORKING PLATE (20 uL per well)


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
sci-lucif-assay2
