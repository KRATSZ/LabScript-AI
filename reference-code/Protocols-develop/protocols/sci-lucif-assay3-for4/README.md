# Luciferase Reporter Assay for NF-kB Activation (up to 4 plates) - Protocol 3: Treatment


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
The protocol performs liquid handling to apply test articles (e.g., serial dilutions of drug candidates) to the reporter cells cultured in 96-well plates.

The luciferase reporter assay is used to investigate the regulation of expression of a gene of interest. This method relies on reporter cells created by stable or transient transfection of a promoter-driven, luciferase-expressing DNA. The bioluminescence proportional to luciferase expression can be quantified to assess the functional connection between the expression of the target gene which is controlled by this promoter, and the factor to be studied which may exhibit a regulatory effect on the cell behaviors at the transcription level. In this particular example, HeLa cells are stably or transiently transfected with an NF-kB promoter-driven, luciferase reporter construct, treated with an NF-kB activator phorbol 12-myristate 13-acetate (PMA), and activation of NF-kB assessed by measuring the luciferase enzymatic activity.

Reagent preparation:
Test articles are diluted in DMEM at the concentrations of interest and pre-loaded in a Corning 96 Well Plate 360 µL Flat (150 μL per well).


### Labware
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons HEPA Filter Module](https://opentrons.com/products/modules/hepa/)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-lucif-assay3-for4/deck.png)


### Reagent Setup
1. Test articles (up to four Corning 96 Well Plate 360 µL Flat, dashed line-encircled) loaded on Slot 1, 4, 7 and 10
2. Reporter cell culture (up to four Corning 96 Well Plate 360 µL Flat) loaded on Slot 2, 5, 8 and 11
3. A NEST 1 Well Reservoir 195 mL for liquid waste loaded on Slot 9
4. Opentrons 96 Tip Rack 300 µL loaded on Slot 3 and 6


### Protocol Steps
1. Remove supernatant in reporter cell culture on Slot 2
2. Transfer test articles on Slot 1 to reporter cell culture on Slot 2 (100 μL per well)
3. Replenish 300 µL tips on Slot 3 (manually)
4. Remove supernatant in reporter cell culture on Slot 5
5. Transfer test articles on Slot 4 to reporter cell culture on Slot 5 (100 μL per well)
6. Replenish 300 µL tips on Slot 3 (manually)
7. Remove supernatant in reporter cell culture on Slot 8
8. Transfer test articles on Slot 7 to reporter cell culture on Slot 8 (100 μL per well)
9. Replenish 300 µL tips on Slot 3 (manually)
10. Remove supernatant in reporter cell culture on Slot 11
11. Transfer test articles on Slot 10 to reporter cell culture on Slot 11 (100 μL per well)
12. Continue cell culture incubation (off deck)


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
sci-lucif-assay3-for4
