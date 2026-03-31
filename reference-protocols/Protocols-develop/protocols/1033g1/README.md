# Cell Viability and Cytotoxicity Assay


### Author
Vasudha Nair


## Categories
* Cell and Tissue Culture
	* Cell and Tissue Culture


## Description
This protocol can be used to measure the viability and cytotoxicity of two different cell types (suspension and adherent) that have been treated with respective drugs, using Cell Viability assay kit (Cell Titer Glo 2.0) and Cytotoxicity assay kit (CellTox Green) from Promega on the OT-2. This protocol is designed for the 96 well plate format and both assays can be processed in the same plate. In the case of K562 cells, the protocol is broken down into 2 main parts: a) Seeding/ Plating of K562 cells and bortezomib additions to the cells b) After 72 hours, completion of both the assays in the same plate i.e. sequential multiplexing of CellTox Green Cytotoxicity Assay and CellTiter Glo 2.0 Assay.


### Labware
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Opentrons 96 Filter Tip Rack 20 µL
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
* [Deck setup for Day 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1033g1/day1.pdf)
* [Deck setup for Day 4](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1033g1/day4.pdf)



### Reagent Setup
[CellTiter-Glo 2.0 100mL Cat No. G9242](https://www.promega.com/products/cell-health-assays/cell-viability-and-cytotoxicity-assays/celltiter_glo-2_0-assay/?catNum=G9242)

[CellTox Green Cytotoxicity assay, 50 mL Cat No. G8742](https://www.promega.com/products/cell-health-assays/cell-viability-and-cytotoxicity-assays/celltox-green-cytotoxicity-assay/?catNum=G8742)

[K562 lymphoblast cells (ATCC, Manassas, VA, USA) (Cat No. CCL243)](https://www.atcc.org/products/ccl-243)

[A549 lung carcinoma cells (ATCC, Manassas, VA, USA) (Cat No. CCL185)](https://www.atcc.org/products/ccl-185)

[Phenol Red Free RPMI 1640 medium (ThermoFisher Scientific 11835030)](https://www.thermofisher.com/order/catalog/product/11835030)

[Phenol Red Free Ham’s F12-K medium (Crystalgen SKU-226-062)](https://crystalgen.com/226-062.html)

[Fetal Bovine Serum (FBS) Not Heat Inactivated (ATCC, Cat No. 30-2020)](https://www.atcc.org/products/30-2020)

Bortezomib 10mM (1mL in DMSO (PS 341) (Selleckchem) Cat No. S1013

Thapsigargin 1mg (Selleckchem) Cat No. 7895



### Protocol Steps
Seeding K562 cells and addition of various concentrations of Bortezomib
On the first day of drug treatment, follow the steps below-
Clean the inside of the robot with 70 % ethanol and turn on the HEPA filter at low fan speed for about an hour before seeding the cells on 96 well plate. Continue to keep the HEPA filter turned on during the duration of setting up the robot with the respective labware, dilutions of the drug(bortezomib) and seeding the cells-drug mix on to the 96 well plate
1.	Take a 24–48 hours old T-75 flask of K562 cells. Take a cell count using the automated Countess 3 machine (Thermofisher Scientific)
2.	2 X 104 cells are to be seeded in each well of the 96 well plate. Adjust the cell volume in 10% RPMI medium in such a way that 60L of cells contain the cell number mentioned above.
3.	The cell suspension was then dispensed in ten 2mL snap-capped tubes and placed in Slot 6 in the tube rack(225L).
4.	The first tube A1 in Slot 7 contains 30L of 10mM Bortezomib
5.	Next, prepare dilutions of various concentrations of bortezomib in 10% RPMI medium (4X concentrations) after preparing the initial stocks ranging from 1nM to 1000M. The molar concentrations of stocks in tubes in positions are - A1 10mM, A2 1000M, A3 100M, A4 10M, A5 1M, A6 100nM B1 10nM and B2 1nM respectively.
6.	The 4X concentrations of bortezomib are prepared in tubes C1 to C6 and D1 to D3 with the following concentrations in the tubes C1 0.4nM, C2 4nM, C3 40nM, C4 159.2nM, C5 200nM, C6 280nM, D1 400nM, D2 (158.95 X 4) nM and D3 (630.95 X 4) nM
7.	For both the initial stocks and the 4X working concentrations, the RPMI diluent in added to respective tubes. Then the bortezomib is added to the tubes and for each dilution, the mix is first pipetted 3-4 times before aspirating the required volume of bortezomib and transferring to the next adjacent tube to get the required concentration.
8.	Once the bortezomib concentrations are prepared, add 4X concentration to the tubes in which cells are already added to result in 1X concentration of the drug (in Slot 7)
9.	For each concentration, mix the cells and drug mix several times. Add the cells-bortezomib mix to each well of 96 well plate in triplicate for one concentration. Continue adding column-wise increasing bortezomib concentrations. Namely A1, B1, C1 of 96 well plate contains control cells. D1, E1 and F1 contains 0.1nM concentration of bortezomib treated cells. The wells in D4, E4 and F4 contains cells with 630.95nM bortezomib concentration. The wells from A5 to C5 contain medium without any cells (medium control).

  After 72 hours of drug treatment, carry out the following steps.
1.	Pick up 20L tip from Slot 10. Transfer 15L of CellTox Green reagent from
B2 of the Opentrons 10 tube rack with Falcon 4X50 mL, 6X15mL Conical-Rack to A1 of 96 well plate placed on the Heater Shaker. Repeat this step to add the reagent to wells B1 to H1, A2 to H2, A3 to H3, A4 to F4, A5 to C5.
2.	After the addition of the reagent, set the Heater Shaker to orbital shaking for 2 minutes at 500 rpm.
3.	After the orbital shaking of the heater shaker is complete, incubate the plate at RT for 15 min.
4.	Remove the plate from the heater shaker and read the fluorescence at 485 nm excitation and 520 nm emission using the Biotek microplate reader.
5.	Place the plate back on the heater shaker and start with additions for the cell viability assay.
6.	Pick up 200L tip from Slot 4. Aspirate 80L of Cell Titer Glo 2.0 reagent from B1 of the Opentrons 10 tube rack and dispense it into A1 well of the 96 well white TC plate on Heater Shaker module. Repeat this step to add the reagent to wells B1 to H1, A2 to H2, A3 to H3, A4 to F4 and A5 to C5.
7.	Once the reagent addition is complete, set the Heater shaker to orbital shaking at 500 rpm for 2 minutes. Incubate at RT for 10 minutes.
8.	Remove the plate from heater shaker and read the plate for luminescence using the Biotek microplate reader.

### Process

1.	Input your protocol parameters
2.	Download your protocol
3.	Upload your protocol into the OT2 app.
4.	Set your deck according to the deck map
5.	Calibrate your labware -- tip racks, Eppendorf and falcon racks, microplate and pipette using the OT2 app. For calibration tips, check out our support articles.
6.	Hit “Run”


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the Troubleshooting Survey (https://protocol-troubleshooting.paperform.co/).




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
1033g1
