# PCR Setup

### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep


## Description
This protocol provides a custom qPCR prep on the OT-2 for up to 4x source 96-well plates into 1x destination 384-wellplate. Mastermix is prepared manually and transferred to each reaction well on the OT-2.

Each protocol run generates an output .csv file that is compatible with Quantstudio instruments. To retrieve the file, launch a Jupyter Notebook server on your robot by following [these instructions](https://support.opentrons.com/s/article/Uploading-files-through-Jupyter-Notebook). The file will be named after the 9000 plate barcode scan, followed by ".csv."

### Labware
* KingFisher 96 Well Plate 200 µL #97002540
* ThermoFisher Microamp 96 Aluminum Block 200 µL #4346906
* Microamp 384 Well Plate 40 µL #4483273
* custom 24 Tube Rack with Custom 2 mL
* KingFisher 96 Deep Well Plate #95040450
* Custom 96 Well Plate 200 µL
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/055b94/deckv2.png)
* yellow on 96-wellplates: sample
* blue on tuberack: prepared mastermix
* purple on strips: mastermix strips for plating (loaded empty)

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
055b94
