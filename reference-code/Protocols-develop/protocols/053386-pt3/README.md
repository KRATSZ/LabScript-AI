# Human Islets - RT Barcoding


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
For detailed protocol steps, please see below. The trash will be used as a waste reservoir for supernatant removal. This protocol is for full plates (96 samples) exclusively. Well 11 of the reservoir will be used for pooled samples.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386-pt3/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386-pt3/reagents.png)


### Protocol Steps
1. To each of the well of the 96-well plate, add 1 μl of uniquely indexed oligo-dT (25 μM).
2. Incubate at 72 oC for 10 min and place the plate on ice.
3. To each well, add 2 μl Smart-seq3 RT mix (62.5 mM Tris-HCl (pH8.3), 75 mM NaCl, 6.25 mM MaCl2, 2.5 mM GTP, 20 mM DTT, 1.25 U/ μl RNase inhibitor, 5 U/ μl Maxima H-minus RT enzyme).
4. Incubate plate in a thermo cycler (off deck). 
5. After reaction, add 60 μl of wash-resuspension buffer into each well.
6. Pool all wells into one reagent reservoir column by column. Wash the first 8-well column with 100μl of wash-resuspension buffer. Pipette up and down. Dispense 50 μl of cell suspension to the reagent reservoir. Transfer the remaining volume ( ~ 100 μl ) from the previous well to the well in the next column.
7. For the last column, transfer the entire volume to the reagent reservoir.
8. Repeat steps 6-7 for an additional two times.
9. Transfer the cell suspension mixture from the reagent reservoir to a 2 ml LoBind tube.
10. Spin cell down at 800g for 6 min.
11. Wash cells once with 500 μl of PBS+0.04%BSA. Spin cell down at 800g for 6 min. Aspirate supernatant.
12. Measure the residual liquid volume in the epp tube. Resuspend cells with the residual volume and transfer all solution into one tube of a 8-tube strip. Wash the epp tube with (80– residual volume) μl of PBS+0.04%BSA buffer and transfer all liquid into the same tube in the 8-tube strip.  



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
053386-pt3
