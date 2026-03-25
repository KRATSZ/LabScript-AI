# Luciferase Reporter Assay for NF-kB Activation - Protocol 1: Cell Culture Preparation


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
The protocol performs liquid handling to prepare a 96-well plate of mammalian cells for luciferase reporter assay.

The luciferase reporter assay is used to investigate the regulation of expression of a gene of interest. This method relies on reporter cells created by stable or transient transfection of a promoter-driven, luciferase-expressing DNA. The bioluminescence proportional to luciferase expression can be quantified to assess the functional connection between the expression of the target gene which is controlled by this promoter, and the factor to be studied which may exhibit a regulatory effect on the cell behaviors at the transcription level. In this particular example, HeLa cells are stably or transiently transfected with an NF-kB promoter-driven, luciferase reporter construct, treated with an NF-kB activator phorbol 12-myristate 13-acetate (PMA), and activation of NF-kB assessed by measuring the luciferase enzymatic activity.

Cell suspension preparation:
Mammalian cervical cancer cell line HeLa (ATCC, Manassas, VA, USA) or HeLa-originated cell line with a sequence of NF-kB response element upstream of luciferase-expressing DNA integrated in the cell’s genome (Cellomics Technology, Halethorpe, MD, USA) is maintained in Dulbecco’s modified Eagle’s medium (DMEM, Thermo Fisher Scientific, Waltham, MA, USA). containing 10% fetal bovine serum and 1% penicillin/streptomycin in humidified 5% CO2 at 37 °C. To prepare cell culture in a 96-well plate, HeLa cells are detached by using trypsin, resuspend in DMEM and poured into a NEST 12-well reservoir. For the assay that requires transient transfection to prepare reporter cells, resuspend 1/4 of cells collected from a confluent 100 mm tissue culture dish (~ 2.2 x 106 cells) in 11 mL DMEM. For the assay using the pre-engineered cell line stably expressing luciferase reporter, resuspend 1/2 of cells collected from a confluent 100 mm tissue culture dish (~ 4.4 x 106 cells) in 11 mL DMEM.


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif/pt1.png)


### Reagent Setup
1. A NEST 12 Well Reservoir 15 mL filled with suspended cells in Well 1 loaded on Slot 3 (CELL STOCK)
2. A Corning 96 Well Plate 360 µL Flat loaded on Slot 6 (WORKING PLATE)
3. An Opentrons 96 Tip Rack 300 µL loaded on Slot 8

### Protocol Steps
1. Transfer cell suspension from CELL STOCK to WORKING PLATE (100 uL per well)


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
sci-lucif-assay1
