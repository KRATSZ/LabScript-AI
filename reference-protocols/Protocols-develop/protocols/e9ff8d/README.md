# 3.1 & 3.2 Incubation Recovery & Pre-Amplification PCR


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* Pre-Amplification


## Description
This is the first of four parts for a custom PCR prep followed by two stage cleanup.


### Modules
* 2x [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* [Eppendorf 96 Well Plate 200 µL on Opentrons Semi-Skirted Adapter](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html)
* [Eppendorf 96 Well Plate 200 µL on Aluminum Block 200 µL](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons 24 Well Aluminum Block with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) or [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/opentrons-200ul-filter-tips/)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e9ff89/pt1+deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e9ff89/pt1+reag.png)


### Protocol Steps
1. 125 uL of recovery agent is added to samples
2. 2 minute delay until a biphasic mixture is attained
3. Visual inspection should occur of the biphasic mixture then resume is selected in the app.
4. Recovery agent is removed from the samples, leaving only a clear liquid in the wells
5. 35 uL of pre-amplification mix is added to the samples
6. Samples are moved to a PCR strip tube prior to thermocycler step as outlined in procedure documentation


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
e9ff8d
