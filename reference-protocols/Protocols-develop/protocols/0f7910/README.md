# Plate Filling with CSV Import


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
Select the format for the source and destination plates. See diagram below. If a 384 plate is selected for destination plate, it should always be in slot 2. If a 96 plate is selected for destination, it should always be in slot 1. Source plates always start from slot 3 to 9, and tip racks are always the same. You can select which tip the protocol will start on in the fields below. If the global transfer volume is over 20ul, then the P300 will be used. If the transfer volume is 20 or less, the P20 will be used. A value of "8" for the starting position of the tip would mean to start H1 of the tip rack, and a value of 10 would mean to start at B2 of the tip rack, since it iterates down by column. The csv should be formatted as such in the header:

```
Source plate barcode, Source plate slot (3-9), Source well, Dest plate barcode, Dest well, Transfer Vol (ul)
```


### Labware
* Corning 384 Well Plate 112 µL Flat
* Corning 96 Well Plate 360 µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0f7910/Screen+Shot+2022-12-20+at+10.41.56+AM.png)


### Protocol Steps
1. Protocol will input the global transfer volume from source plates to destination plates in accordance with the csv.


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
0f7910
