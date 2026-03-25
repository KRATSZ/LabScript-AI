# Kapa Bead Clean Up


### Author
[Opentrons](https://opentrons.com/)


## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs a post-amplification 1X Purification using AMPure Beads. For detailed protocol steps, please see below.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Agilent 96 Well Plate 270 µL
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/kapa-amp/Screen+Shot+2024-01-25+at+11.44.39+AM.png)



### Protocol Steps
1. Premix beads, 200ul, 15-20x
2. Add 90ul (50ul sample in there), Mix at 110ul, 7-10x
3. 5 minute incubation
4. Engage magnet, delay 3 minutes
5. Remove 140ul supernatant into waste. Go down again.
6. 200ul ethanol washes x2. Use one set of tips to add ethanol from top of the well.
7. 2-3 minute dry time.
8. Disengage magnet
9. Resuspend beads with eb, mix 20 times, aspirate low dispense high, default flow rate.
10. Incubate 2 minutes.
11. Engage magnet
12. 20ul to pcr strip tube plate



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
kapa-amp-cleanup
