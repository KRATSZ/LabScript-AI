# Sample Prep with DMSO and CSV Input


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol preps up to two 96 well plates with reagent and sample. The protocol takes a csv as input to determine which wells in the middle rack (see below) will be populated. The csv must include the header, with the following order in the header: `vial_id, parent_well, dmso_volume, daughter_column`. The protocol pauses midway through after the samples are placed and mixed in the middle plates for the user to inspect before resuming.


### Labware
* CRO Vial Holder
* Micronic Tube Rack
* [Opentrons 6 Tube Rack 50mL](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)




### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/01b4a2/Screen+Shot+2022-11-01+at+4.27.35+PM.png)


### Protocol Steps
1. Read in CSV/Excel file that has a list of vial_ids, parent_wells, dmso_volumes, & daughter_columns.
2. Pick up new 1000 uL tip.
3. Take specified dmso_volume from the DMSO in position A1 of 50 mL conical holder in slot 8.
a. Note: The volume will often be greater than 1000 uL.
4. Touch tips to remove droplets from pipette tip.
5. Add specified dmso_volume to parent_well position of CRO vial holder in slot 9.
6. Mix the vial at parent_well position of the CRO vial holder in slot 9 using half the dmso_volume added (same tip).
7. Touch tip to remove droplets from pipette tip.
8. Repeat steps 2-7 for all entries in the csv/excel file.
9. Pause to allow visual inspection of the vial.
10. Resume protocol after inspection.
11. Pick up new 300 uL Tip.
12. Aspirate 240 uL of compound from parent_well position of CRO vial holder in slot 9.
13. Touch tips to remove droplets from the pipette tip.
14. Dispense 30 uL into all tubes of daughter_column and touch tips after each dispense.
a. E.g., A1, B1, C1, D1, E1, F1, G1, & H1
15. Discard tip.
16. Repeat steps 11-15 for all entries in the csv/excel file.


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
01b4a2
