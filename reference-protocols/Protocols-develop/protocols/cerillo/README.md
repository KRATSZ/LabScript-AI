# Cerillo Plate Reader Protocol


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol preps a 96 200ul Armadillo plate to be used directly on the Cerillo Stratus. For detailed protocol steps, please see below.

[For an example csv, please see here.](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cerillo+csv.xlsx)

Note: keep the x in the top left corner. If you would not like to put a volume in a well (ie skipping a well), then replace any number with an "x".


### Labware
* Cerillo Stratus Armadillo Flat Bottom Plate 96well 200uL
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cerillo/deck.png)


### Protocol Steps
1. If user decides, buffer is added to deepwell plate according to buffer csv (single-channel).
2. If user decides, stock is added to deepwell plate according to stock csv (single-channel).
3. Stock and buffer are mixed with multi-channel pipette, then transferred to reader.
4. Cells premixed with mulit-channel.
5. 180ul of cells are transferred to reader, mixing 3 times when mixed in diluted stock.  



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
cerillo
