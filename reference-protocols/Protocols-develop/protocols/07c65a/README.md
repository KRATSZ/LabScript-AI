# Sample Dilution with CSV Input


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol dilutes sample with water at 4C, mixing with the transfer volume for 3 repetitions upon dispensing. The multi-channel pipette will be used as a single for this protocol.

* `CSV Sample Format`: Below, you should upload a .csv file formatted in the following way, being sure to include the header line:
```
Destination Well, Transfer Volume
A1, 5
B1, 2
etc.
```

### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* Armadillo 96 Well Plate 200 µL PCR Full Skirt #AB2396
* [Opentrons 24 Well Aluminum Block with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/07c65a/deck.png)


### Protocol Steps
1. Add water to sample according to csv
2. Mix for 3 repetitions
3. Repeat until csv is completed


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
07c65a
