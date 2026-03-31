# DNA Extraction with Heater Shaker - Part 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This protocol takes up to 3 csv files per source plate to dispense into a 96 well plate on the heater shaker module. Samples can be in any order in the source plate as long as they are specified in the csv, but will always be loaded into the final plate by column. A maximum number of 90 samples can be loaded into the 96 well plate on the heater shaker, leaving room for the 6 controls (and subsequently 90 samples between all 3 csv files). Note: for reagent 4 in columns 4 & 5, reagent 5 in columns 6 & 7, and reagent 6 in columns 8 & 9, split the total calculated reagent volume EQUALLY between the pair of columns, as the protocol will circle between the pair of columns as the source.

* The first row of all 3 csv files should be populated with the header, with the relevant parsing information to start in row 2 of each csv file. The header should consist of the following in the following order: ```barcode, rack_num, sample_rack_row, sample_rack_col,plate_row, plate_col, dna_extract_row, dna_extract_col```. All relevant information for the protocol is just taken from the ```dna_extract_row, dna_extract_col``` columns. The number of csv files must equal the number of source plates selected below.


---

### Modules
* [Heater-Shaker Module](https://shop.opentrons.com/heater-shaker-module/)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Abgene 96 deep well plate](https://assets.fishersci.com/TFS-Assets/LCD/Datasheets/Abgene-96-Well-Plate-Datasheet.pdf)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [P300 Single Channel Pipette](link to pipette on shop.opentrons.com)
* [P300 Multi Channel Pipette](link to pipette on shop.opentrons.com)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0530d8/Screen+Shot+2022-11-07+at+11.04.58+AM.png)

### Reagent Setup
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0530d8/Screen+Shot+2022-11-01+at+11.46.43+AM.png)

---

### Protocol Steps
1. Sample added to heater shaker (HS) plate
2. Controls added to HS plate.
3. 50ul of reagent in column 1 of the reagent plate is loaded into samples and control on HS plate.
4. Heater shaker set at 37C, 2000 RPM for 60 minutes
5. 60ul of reagent in column 2 of the reagent plate is loaded into samples and control on HS plate.
6. Heater shaker set at 55C for 30 minutes

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
0530d8
