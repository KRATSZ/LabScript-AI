# Two 96 Deepwell to PCR Plate (Vertical)


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
Two 96 wells are consolidated in one 96 PCR plate. Number of sets is equal to a group of 4 columns, taking 20ul from the 1st and fourth column of that set, and 2ul from columns 2 and 3 from that set. Then, 4 tips are picked up from tip rack on slot 6, and the exact same process is repeated for the remaining four wells under the 8 filled wells in both the source and destination plates.


### Labware
* Quintara Vertical Plate 192 Wells
* Quintara 12 Reservoir 15000 µL
* Double Pcr 96 Well Plate 300 µL
* Appliedbiosystem 384 Well Plate 40 µL
* Quintara 96 Well Plate 300 µL
* Quintara Vertical Plate 192 Wells
* Deepwell 96 Well Plate 2000 µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara_onsite_part2/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara-onsite/pt2/deck.png)


### Protocol Steps
1. 20, 2, 2, and 20ul are taken from 4 columns in a set and dispensed into the starting destination well (change tips).
2. Step 1 is repeated for the desired number of sets (one set per destination column).
3. 4 tips are picked up and steps 1 & 2 are repeated for the remaining four wells under the 8 already filled wells in that set.


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
quintara_onsite_part2
