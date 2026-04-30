# Mastermix Filling 9 Plates


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
1 of 6 mastermixes is filled into all 108 columns in all 9 plates from two wells of a reservoir. Pipette will automatically be assigned depending on the mastermix selected, and multi-dispensing is installed when possible to the pipette maximum volume. Mastermix is taken back and forth between the two mastermix wells (aspirate A1, aspirate A2, aspirate A1,..., etc.), so fill mastermix source columns in the reservoir evenly. Mastermix details are included in the dropdown menu.



### Labware
* Quintara Vertical Plate 192 Wells
* Quintara 12 Reservoir 15000 µL
* Double Pcr 96 Well Plate 300 µL
* Appliedbiosystem 384 Well Plate 40 µL
* Quintara 96 Well Plate 300 µL
* Quintara Vertical Plate 192 Wells
* Deepwell 96 Well Plate 2000 µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara-onsite/pt3/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara-onsite/pt3/liquids.png)


### Protocol Steps
1. Aspirate mastermix volume according to mastermix selected.
2. Dispense into all wells, multi-dispensing if possible.


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
quintara_onsite_part3
