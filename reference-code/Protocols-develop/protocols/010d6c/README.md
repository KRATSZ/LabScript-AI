# Ribogreen Assay


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs a Ribrogreen assay - for detailed protocol steps, please see below. There is the option to perform duplicate/triplicate plating. The csv for sample input should include `source slot, source well, destination well` in the header.


### Labware
* Corning 12 Reservoir 2000 µL
* Nunc 96 Well Plate 400 µL
* Opentrons 15 Tube Rack with eppendorf 5 mL
* Pyramid 96 Well Plate 2000 µL
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 24 Tube Rack with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010d6c/Screen+Shot+2023-11-27+at+1.39.18+PM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/010d6c/reagents.png)


### Protocol Steps
1. Calibration standard preparation in deep well plate (matrix buffer addition)
2. Calibration standard preparation in deep well plate (4 ug/mL calibration stock addition)
3. Calibration standard plating (duplicate or triplicate)
4. Sample plating (duplicate or triplicate)
5. Triton addition
6. TE addition
7. Heating at 37 C for 10 minutes
8. Dye addition



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
010d6c
