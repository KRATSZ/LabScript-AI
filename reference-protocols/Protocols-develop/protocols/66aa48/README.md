# CSV Consolidation


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Cherrypicking


## Description
This protocol allows the robot to create up to 4 different pooling samples by consolidating cherrypicked wells from a 96 tall-well plates. The user will need upload one CSV each for increase, no change, decrease, and inactive property changes. Each CSV will contain information of the wells from which to be picked. See Additional Notes for the format of the CSVs, as well as the arrangement of pooling tubes in the Opentrons 4x6 2ml Eppendorf tuberack. If you would like to skip a pool as specified by 1 of the 4 CSV files, upload an empty CSV file corresponding to that pool.

Your CSV files should contain source wells of the 96-well source plate each on its own line, as in the following:  
```
A2
A3
A4
A7
A8
B3
B5
```

The pooling tubes are seated in the Opentrons tube rack according to the following setup:
* inactive: tube A1
* decrease: tube B1
* no change: tube C1
* increase: tube D1


### Labware
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 24 Tube Rack with Eppendorf 2 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P50 Single Channel Electronic Pipette](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


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
66aa48
