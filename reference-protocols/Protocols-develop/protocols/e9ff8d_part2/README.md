# 3.3 DNA Cleanup – SPRIselect


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Purification
	* DNA Cleanup


## Description
This is the second of four parts for a custom PCR prep followed by two stage cleanup. This is the first of two cleanups.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* [Biorad 96 Well Plate 200 µL to hold Generic PCR Strips](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Eppendorf 96 Well Plate 200 µL on Opentrons Semi-Skirted Adapter](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html)
* [Eppendorf 96 Well Plate 200 µL on Aluminum Block 200 µL](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Plates-44516/Eppendorf-twin.tec-PCR-Plates-LoBind-PF-58208.html)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons 24 Well Aluminum Block with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) or [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/opentrons-200ul-filter-tips/)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e9ff89/pt2+deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/e9ff89/pt2+reag.png)


### Protocol Steps
1. SPRI beads are mixed prior to 126 uL being added to samples
2. SPRI and samples are mixed
3. Beads are left to incubate for 5 minutes
4. Magnetic module is engaged for 5 minutes to separate beads
5. Supernatant is removed and disposed of
6. Beads are washed twice with 200 uL of ethanol, disposing of ethanol each time
7. Magnetic module is disengaged
8. 101 uL of elution solution is added to the samples and mixed
9. Samples are left to elute for 2 minutes
10. Magnetic module is engaged for 5 minutes to separate beads
11. 100 uL of now eluted sample is transferred to column 2 on the 96 well plate


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
e9ff8d_part2
