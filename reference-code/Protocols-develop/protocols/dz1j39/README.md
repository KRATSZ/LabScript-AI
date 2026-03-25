# Cell Viability and Cytotoxicity Assay


### Author
Opentrons




## Categories
* Cell and Tissue Culture
	* Cell and Tissue Culture


## Description
This protocol can be used to measure the viability and cytotoxicity of two different cell types (suspension and adherent) that have been treated with respective drugs, using Cell Viability assay kit (Cell Titer Glo 2.0) and Cytotoxicity assay kit (CellTox Green) from Promega on the OT-2. This protocol is designed for the 96-well plate format and both assays can be processed in the same plate. In the case of A549 cells, the protocol is broken down into 3 main parts: a) Seeding/ Plating of A549 cells on Day 1 followed by b) treatment with thapsigargin on the second day c) After 72 hours of treatment, completion of both the assays in the same plate i.e., sequential multiplexing of CellTox Green Cytotoxicity Assay and CellTiter Glo 2.0 Assay.


### Labware
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Opentrons 96 Filter Tip Rack 20 µL
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
* [Day 1 Deck Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/Cell+Viability+and+Cytotoxicity+Assay_A549_Day1.docx.pdf)
* [Day 2 Deck Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1033g1/day2.pdf)
* [Day 4 Deck Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/Cell+Viability+and+Cytotoxicity+Assay_A549_Day4.docx.pdf)


### Reagent Setup
* [Please find the reagent setup here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1033g1/reagents.pdf)


### Protocol Steps
Measurement of viability and cytotoxicity of an adherent cell line, A549 cells, treated with thapsigargin
Seeding A549 cells and addition of various concentrations of Thapsigargin on the second day after the cells have adhered to the 96 well TC plate.
On the first day of plating and the second day when the drug additions are to take place, follow the steps below-
Clean the inside of the robot with 70 % ethanol and turn on the HEPA filter at low fan speed for about an hour before seeding the cells on 96 well plate. Continue to keep the HEPA filter turned on during the duration of setting up the robot with the respective labware, dilutions of the drug (thapsigargin)on the second day and addition of the drug on to the 96 well plate
1.	Take a 24–48 hours old T-75 flask of A549 cells. Take a cell count using the automated Countess 3 machine (Thermofisher Scientific) after treating the cells with Tryple Express enzyme and dislodging the adherent cells.
2.	8000 cells are to be seeded in each well of the 96 well plate. Adjust the cell volume in 10% Ham’s F12K medium in such a way that 60 microL of cells contain the cell number mentioned above.
3.	The cell suspension was then dispensed in ten 1.5mL snap-capped tubes and placed in Slot 6 in the tube rack(225microL).
4.	The medium was added in wells A5 to C5 as negative control
5.	On the second day, roughly after 12 to 16 hours of seeding, the drug dilutions and additions are completed.
6.	The first tube A1 in Slot 7 contains 35microL of 1mM Thapsigargin.
7.	Next, prepare dilutions of various concentrations of thapsigargin in 10% Ham’s F12K medium (4X concentrations) after preparing the initial stocks ranging from 10nM to 100microM. The molar concentrations of stocks in tubes in positions are - A1 1mM, A2 100microM, A3 10microM, A4 1microM, A5 100nM, A6 50nM and B1 10nM.
8.	The 4X concentrations of thapsigargin are prepared in tubes C1 to C6 and D1 to D6 with the following concentrations in the tubes C1 1.56nM, C2 3.12nM, C3 6.24nM, C4 12.52nM, C5 25nM, C6 50nM, D1 100nM, D2 200nM, D3 400nM, D4 800nM D5 1600nM and D6 2000nM
9.	For both the initial stocks and the 4X working concentrations, the Ham’s F12 K diluent in added to respective tubes. Then the thapsigargin is added to the tubes and for each dilution, the mix is first pipetted 3-4 times before aspirating the required volume of thapsigargin and transferring to the next adjacent tube to get the required concentration.
10.Once the 4X concentrations are prepared, prepare 2X concentrations of the   drug. First, 100microL of medium is added to tubes C1, C3, C5 and D1 to D6  in Slot 6. Next 100microL of 4X concentration of thapsigargin is transferred from tubes in Slot7 to tubes in Slot 6 to result in 2X concentration.  
11.For each concentration, mix the drug several times by aspirating and dispensing in the same tube. Add the equal volume of 2X thapsigargin to each well of 96 well plate in triplicate for one concentration in which cells are seeded. This will result in 1X concentration of the drug used for the study. Continue adding column-wise the increasing concentrations of thapsigargin. Namely A1, B1, C1 of 96 well plate contains control cells. D1, E1 and F1 contains 0.39nM concentration of thapsigargin treated cells. The wells in D4, E4 and F4 contains cells with 500nM thapsigargin concentration. The wells from A5 to C5 contain medium without any cells (medium control).
After 72 hours of drug treatment, carry out the following steps.
1.	Pick up 20microL tip from Slot 10. Transfer 15microL of CellTox Green reagent from
B2 of the Opentrons 10 tube rack with Falcon 4X50 mL, 6X15mL Conical-Rack to A1 of 96 well plate placed on the Heater Shaker. Repeat this step to add the reagent to wells B1 to H1, A2 to H2, A3 to H3, A4 to F4, A5 to C5.
2.	After the addition of the reagent, set the Heater Shaker to orbital shaking for 2 minutes at 500 rpm.
3.	After the orbital shaking of the heater shaker is complete, incubate the plate at RT for 15 min.
4.	Remove the plate from the heater shaker and read the fluorescence at 485 nm excitation and 520 nm emission using the Biotek microplate reader.
5.	Place the plate back on the heater shaker and start with additions for the cell viability assay.
6.	Pick up 200microL tip from Slot 4. Aspirate 80microL of Cell Titer Glo 2.0 reagent from B1 of the Opentrons 10 tube rack and dispense it into A1 well of the 96 well white TC plate on Heater Shaker module. Repeat this step to add the reagent to wells B1 to H1, A2 to H2, A3 to H3, A4 to F4 and A5 to C5.
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
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the Troubleshooting Survey (https://protocoltroubleshooting.paperform.co/).



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
dz1j39
