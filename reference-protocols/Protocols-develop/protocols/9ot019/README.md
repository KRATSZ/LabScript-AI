# Glycerol Stock


### Author
Tim Dobbs




## Categories
* General Liquid Handling
	* General Liquid Handling


## Description
This is a flexible protocol for making glycerol stocks of E. coli cultures for long-term storage in a -80C freezer. The protocol expects that you've grown the strains in liquid culture to an acceptable optical density, and prepared a sterile solution of 50% glycerol, 50% deionized water.

The protocol loads 500ul of liquid culture and 500ul of glycerol into a cryo tube, which you should then cap, label, and store in your -80C freezer. By default, 3 replicates of each strain are made. The number of samples and the number of replicates can be changed and the protocol will automatically calculate the number of cryo tubes you need. The protocol will throw an error there are too many samples to fit on the deck.

In our experience, this protocol starts to become worth using if you have more than ~20 total samples. Less than that and it's faster to hand-pipette.

Watchouts:
- Make sure the de-cap all of your cryo tubes and the 50ml conical glycerol tube before running. If your liquid cultures are in tubes, de-cap those too.
- The protocol comments will display the final platemap of the cryo tubes. Make sure to label your tubes before taking them out or closing the window.


### Labware
* Cryo 35 Tube Rack with Nunc 1.8 mL #BioArtBot
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)


### Pipettes
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
[deck](https://drive.google.com/open?id=1KDbr6pEu0CT6NpcVpTAkZRpqyCJ2hkdY)


### Reagent Setup
[reagents](https://drive.google.com/open?id=1jAmqDEEdMpelM5_yBAuGAZbuoY282pav)


### Protocol Steps
1. Load glycerol into all cryo tubes
2. Load each strain into the appropriate number of cryo tubes, as determined by the number of replicates requested. The tip is changed between strains. 


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
9ot019
