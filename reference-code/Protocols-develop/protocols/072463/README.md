# Simplified Fe Quantification Assay


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs the Simplified Fe Quantification Assay. If in Test Mode, the protocol will skip over all incubations and temperature changes. The protocol will automatically pause if tips have to be replaced, prompting the user. Pauses are included according to the protocol.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* RRL 1 Well Plate 180000 µL #v 1.0
* RRL Custom 40 Well Plate 1500 µL #v 1.0
* Zinsser 96 Well Plate 1898 µL
* Hellma 96 Well Plate 300ul
* [USA Scientific 96 Deep Well Plate 2.4 mL #1896-2000](https://www.usascientific.com/2ml-deep96-well-plateone-bulk.aspx)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/072463/Screen+Shot+2022-12-14+at+8.32.53+AM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/072463/Screen+Shot+2022-12-13+at+12.50.20+PM.png)
![reagents2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/072463/Screen+Shot+2022-12-13+at+12.50.41+PM.png)
![reagents3](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/072463/Screen+Shot+2022-12-13+at+12.50.51+PM.png)


### Protocol Steps
1. User calibrates protocol on deck.
2. Deck starts with samples in the sample block and empty digestion plate in the heating module. The reagent block is on the deck but only has water in Well A1.
3. Pipette 5-20 uL of water in triplicate from the reagent block into the digestion plate. (1 x 30 uL tip). Make the pipetted volume user selectable and consistent for all samples.
4. Pipette 5-20 uL (same as in step 3) of each sample in triplicate from the sample block into the digestion plate. (1-24 x 30 uL tips)
5. Add 1200 uL of nitric acid from the acid block into each well of the digestion plate. The solution is mixed 15 times at 200ul with the multi-channel pipette
6. Pause so user can cover the digestion plate.
7. Raise heating block temperature to 95 °C (this is actually now variable, per email on 12/15/22) and maintain for 12 h (this is actually now variable, per email on 12/15/22).
8. Cool heating block to room temperature. Wait for 1 h to ensure all samples reach room temperature.
9. Pause until user removes the cover from the digestion plate and places the reagent block and analysis plate on the deck.
10. Transfer triplicate 10 uL aliquots from the 7 Fe calibration standards in the sample block into the Quartz analysis plate in slot 2. (21 wells; 7 x 30 uL tips)
11. All columns in digestion plate mixed with multi-channel pipette.
12. Transfer 5-20 uL aliquots from each sample in the digestion plate into the Quartz analysis plate in slot 2. (6-75 wells; 6-75 x 30 uL tips).
13. Pause for user to place the Quartz analysis plate in the heating module.
14. Raise heating block temperature to 95 °C and maintain for 1 h.
15. Cool heating block to room temperature. Wait for 1 h to ensure all samples reach room temperature.
16. Pause for user to place the Quartz analysis plate in slot 2 and place the digestion plate in the heating module.
17. Add 46 uL of water from the reagent block to each well in the Quartz analysis plate in slot 2. (27-96 wells; 1 x 300 uL tip)
18. Add 30 uL reagent A from the reagent block to each well in the Quartz analysis plate in slot 2. (27-96 wells) a. Mixing step.
19. Wait 1 h for reagent A to react with Fe in each well.
20. Add 49 uL of reagent B from the reagent block to each well in the Quartz analysis plate in slot 2. (27-96 wells; 1 x 300 uL tip)
21. Add 75 uL of reagent C from the reagent block to each well in the Quartz analysis plate in slot 2. (27-96 wells) a. Mixing step.
OPTIONAL (yes/no variable) – transfer 200-900 uL from each well of the digestion plate (slot 2) into the sample storage block (slot 6). Write this so that 200 uL are transferred now because we are using a standard plate. Later will be changed to 900 uL when we have custom labware with 1 mL shell vials. Samples may be stored for additional measurements for up to 2 weeks. OT2 provides a CSV file with sample/replicate labels corresponding to positions in the sample storage block. (6-75 x 300 uL tips)


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
072463
