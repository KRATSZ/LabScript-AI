# CSV Plate Filling - Upgrade for OT2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* CSV Transfer

## Description
This is an OT-2 compatible protocol that first transfers media and then up to 35 different antibiotics plus a barcoding dye to the wells of one to six 96 well plates based on an input CSV file. If there are more entries once the plate(s) have been filled the user is asked to replace the plates with fresh ones, as well as used tips, and the process continues until all rows of the input file have been processed.

Each line in the csv corresponds to the transfers to a well on the plates. The plates are ordered sequentially from slot 1 to slot 6 meaning that the first 96 rows of the csv (excluding the header) correspond to the 96 wells on plate 1, and so on.

Explanation of protocol parameters:
* `input .csv file`: Here you should upload a .csv file formatted in the following way, being sure to include the header line: The first column is an identifier and is discarded by the protocol (but must be included in order for the file to be processed correctly), the 2nd column is the transfer volume of M9 media that is stored in 3 50 mL tubes on the tuberack on slot 8. The remaining columns up to n-1 are antibiotics stored on 15 mL tuberack 1 and 2 (see below). The nth column is the volume of barcoding dye.
```
,M9,antibiotic 1, antibiotic 2, ... , antibiotic n, barcoding dye
99999,50,0,0,...,0,50
100,90,10,0,...,0,0
```
* `20 uL pipette tips`: Brand of pipette tips, either Opentrons or BrandTech 20 uL tips
* `300 uL pipette tips`:  Brand of pipette tips, either Opentrons or BrandTech 300 uL tips
* `Number of plates`: The number of Nunc 96 well plates on the deck per run, may range from one to six
* `Height offset for dispensing antibiotics into target wells [mm]`: Offset for dispensing antibiotics into wells in mm (above the original level which was the calculated liquid level in the well minus 0.4 mm).

---

### Labware
* [Opentrons 20 uL tipracks](https://shop.opentrons.com/opentrons-20-l-tips-160-racks-800-refills/)
* [300 uL tipracks](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)
* [BrandTech 20 uL tipracks](https://brandtech.com/product/standard-tips/)
* [BrandTech 300 uL tipracks](https://brandtech.com/product/standard-tips/)
* [Nunc 400 µL 96 well plate](https://www.thermofisher.com/us/en/home/life-science/cell-culture/cell-culture-plastics/nunc-plate-selection-guide.html#!/n_format:96)
* [Opentrons tuberacks](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons tubes](https://shop.opentrons.com/consumables/)
* [Falcon tubes](https://ecatalog.corning.com/life-sciences/b2c/US/en/Liquid-Handling/Tubes%2C-Liquid-Handling/Centrifuge-Tubes/Falcon%C2%AE-Conical-Centrifuge-Tubes/p/falconConicalTubes)

### Pipettes
* [P20 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [P300 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* M9 media in 50 mL tubes on slot 8
* Antibiotics in 15 mL tuberack on slot 9 and 7 and the 15 mL tubes on slot 8.
* Barcoding dye in the last 15 mL tube, e.g. the 6th 15 mL tube on the tuberack on slot 8 if the maximum number of antibiotics slots are filled.

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/017860/deck.jpg)
Slots:
1. Nunc 96 well plate 1
2. Nunc 96 well plate 2 (optional)
3. Nunc 96 well plate 3 (optional)
4. Nunc 96 well plate 4 (optional)
5. Nunc 96 well plate 5 (optional)
6. Nunc 96 well plate 6 (optional)
7. Tuberack with 15 mL tubes antibiotic tuberack (#2)
8. Tuberack 4x50 mL/6x15 mL tubes - Media and antibiotics (#3)
9. Tuberack with 15 mL tubes antibiotic tuberack (#1)
10. 20 µl tiprack
11. 300 µL tiprack


### Reagent Setup
* 15 ml tuberack antibiotics #1 on slot 9: Antibiotics 1 to 15
* 15 ml tuberack antibiotics #2 on slot 7: Antibiotics 15 to 30
* Mixed tuberack antibiotics #3 on slot 8: Tube 1-6: Antibiotics and barcoding dye, Tube A3-A4: M9 media
![Mixed tuberack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/017860/mixed_rack_slot8.jpg)

---

### Protocol Steps
1. The protocol transfers M9 to the plate wells according to the csv specification
2. The protocol transfers mixes of different antibiotics to the plate wells according to the CSV specification.
3. The protocol transfers the barcoding dye to the specified well(s)
4. If there are more rows in the csv than there are plate wells the user is asked to replace the plates and the spent tips and the process restarts from step 1.

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
017860
