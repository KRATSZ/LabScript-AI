# Luciferase Reporter Assay for NF-kB Activation - Protocol 3: Treatment


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description

The protocol performs liquid handling to apply test articles (e.g., serial dilutions of drug candidates) to the reporter cells cultured in a 96-well plate.

The luciferase reporter assay is used to investigate the regulation of expression of a gene of interest. This method relies on reporter cells created by stable or transient transfection of a promoter-driven, luciferase-expressing DNA. The bioluminescence proportional to luciferase expression can be quantified to assess the functional connection between the expression of the target gene which is controlled by this promoter, and the factor to be studied which may exhibit a regulatory effect on the cell behaviors at the transcription level. In this particular example, HeLa cells are stably or transiently transfected with an NF-kB promoter-driven, luciferase reporter construct, treated with an NF-kB activator phorbol 12-myristate 13-acetate (PMA), and activation of NF-kB assessed by measuring the luciferase enzymatic activity.

Reagent preparation:
PBS used for washing (50 uL per sample, 6.5 mL sufficient for 96 samples) is filled in the first well of a NEST 1 Well Reservoir 195 mL. Test articles are diluted in DMEM at the concentrations of interest and pre-loaded in a Corning 96 Well Plate 360 µL Flat (150 uL per well).


### Labware
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif/pt3.png)


### Reagent Setup
1. A NEST 12 Well Reservoir 15 mL filled with PBS in Well 1 loaded on Slot 3 (REAGENT STOCK)
2. A Corning 96 Well Plate 360 µL filled with test articles loaded on Slot 5
3. Cell culture prepared in a Corning 96 Well Plate 360 µL Flat loaded on Slot 6 (WORKING PLATE)
4. A NEST 1 Well Reservoir 195 mL for liquid waste loaded on Slot 9
5. Opentrons 96 Tip Rack 300 µL loaded on Slot 1, 4, 8 and 11


### Protocol Steps
1. Remove medium in cell culture: transfer supernatant from WORKING PLATE to WASTE
2. Wash cells:
Transfer PBS from REAGENT STOCK to WORKING PLATE (50 uL per well)
Transfer supernatant from WORKING PLATE to WASTE
3. Apply treatment: transfer test articles from TREATMENT to WORKING PLATE (100 uL per well)


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
sci-lucif-assay3
