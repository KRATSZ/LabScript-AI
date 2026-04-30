# Pooling and Normalization via CSV


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs a pooling or normalization protocol depending on the user's selection. Please format the csv to the examples below (two header rows before the transfer information). The normalization csv should include "normalization", and the pooling csv should include the word "pooling" in the top row.  Volumes must be over 1.0ul for all transfers. Volumes should be "0" if they are to be skipped for a well.


* [Normalization CSV Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0a9b58/normalization.png)
* [Pooling CSV Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0a9b58/pooling.png)




### Labware
* [Agilent 1 Well Reservoir 290 mL #201252-100](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup

* This is the deck setup for the normalization protocol. For the pooling protocol, the reservoir is not needed in slot 1, and the tip rack in slot 5 is not needed.
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0a9b58/Screen+Shot+2023-04-24+at+4.01.28+PM.png)


### Protocol Steps
1. For normalization protocol: transfer water (one tip), transfer dna (one tip per well) according to csv.
2. For pooling protocol: transfer dna according to csv.


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
0a9b58
