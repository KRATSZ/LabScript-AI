# PCR Prep and PCR


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR


## Description
This protocol begins with mastermix addition, then proceeds to do pcr. Note: mastermix is loaded on the temperature module on slot 4. One column of mastermix is for 24 (3 columns) of samples. That is, for 48 samples, you should load two columns of mastermix. For 48-72 samples, 3 columns of mastermix, so on and so forth. If there are multiple columns of mastermix, the volume should be split evenly between the number of columns you are running. For unfilled columns, mastermix should always be placed in column 6 of the plate on slot 3.

If you select tube racks for mastermix, each tube accomodates 24 samples in slot 3, and should be placed in the first row (maximum 4 tubes in first row for 96 samples). Mastermix volume should be distributed equally for all tubes in the first row. 

The NEST 96 100ul plate should be placed on the 96 aluminum adaptor on the temperature module, which will be at 4C to keep the temperature cool.

See below for the two types of deck states before pcr. If you select the tube rack deck state, tubes should be placed by row in one tube rack before moving onto another, in the order of slots 4, 5, 1, 2. That is, for 27 samples, you should fill the entire first tube rack on slot 4, then the first 3 tubes in the first row of the tube rack in slot 5.



### Modules
* [Opentrons Thermocycler Module](https://shop.opentrons.com/thermocycler-module-1/)
* [Opentrons Temperature Module](https://shop.opentrons.com/thermocycler-module-1/)


### Labware
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [Opentrons 24 Well Aluminum Block with NEST 1.5 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ca318/Screen+Shot+2023-04-03+at+2.32.01+PM.png)

![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ca318/Screen+Shot+2023-04-03+at+2.33.02+PM.png)



### Protocol Steps
1. Sample added (if needed).
2. Mastermix added.
3. Lid of thermocycler closes, pcr.


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
0ca318
