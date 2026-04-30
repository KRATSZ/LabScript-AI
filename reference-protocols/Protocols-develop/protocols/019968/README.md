# Methanol Dilution for LCMS Analysis


### Author
[Opentrons](https://opentrons.com/)


## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol either perfors single, or double dilution of sample with methanol and standard for LCMS analysis. For more details, please see below.


### Labware
* Waters 48 Tube Rack with ThermoFisher 0.3 mL #700011047
* [Opentrons 24 Well Aluminum Block with Generic 2 mL Screwcap](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup

* This is the single dilution deck setup. For the double dilution workflow, replace the waters 48 racks on slots 1 and 2 with Opentrons 24 tuberack aluminum as seen in slots 4 and 5.
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/019968/deck.png)



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
019968
