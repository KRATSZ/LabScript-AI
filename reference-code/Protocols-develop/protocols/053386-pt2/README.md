# Human Islets - Sample Barcoding Oligos


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
For detailed protocol steps, please see below. The trash will be used as a waste reservoir for supernatant removal. This protocol is for full plates (96 samples) exclusively. Well 12 of the reservoir will be used for pooled samples. 


### Labware
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386-pt2/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386-pt2/reagents.png)


### Protocol Steps
1. In each well of 96-well plate, add 1 μl of 0.4 μM of SBO. SBOs are unique to each well.
2. Pipette the cells up and down 10x with the pipette set to 50 μl in volume.
3. Wash the cells by adding 150 μl of wash-resuspension buffer in each well.
4. Spin at 800g for 6 min.
5. Aspirate and discard 150 μl of supernatant.
6. Repeat steps 3-5 for additional two washes.
7. Pool all wells into one reagent reservoir column by column. Wash the first 8-well column with 150μl of Smart-seq3 lysis buffer per well (Smart-seq3 lysis buffer 1. (12.5% PEG 8000, 0.1% Triton, 0.5U/μl RNase inhibitor, 1.25 mM dNTP). Pipette up and down. Dispense 50 μl of cell suspension to the reagent reservoir. Transfer the remaining volume (~150 μl) from the previous well to the well in the next column.
8. For the last column, transfer the entire volume to the reagent reservoir.
9. Repeat steps 7-8 for an additional two times.
10. Transfer the cell suspension mixture from the reagent reservoir to a 5 ml LoBind tube.
11. Count cells. Adjust cell concentration to 1,000 cells/μl with Smart-seq3 lysis buffer.
12. To each well of a skirted twin.tec 96-well LoBind plate, add 2 μl of cell suspension. Distribute cells into 95 wells. Add 2 μl of Smart-seq3 lysis buffer into one additional well as one negative control.




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
053386-pt2
