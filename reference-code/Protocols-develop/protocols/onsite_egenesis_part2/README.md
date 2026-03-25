# Ligation Sequencing Amplicons Native Barcoding


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
For a detailed description of this protocol, please refer to the [Ligation Sequencing Amplicons Native Barcoding](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis_part2/manual.pdf)

Note: select the barcode numbered well to start from counting by column. "1" would be A1, "8" would be H1, "10" would be B2, so on and so forth.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Barcode 96 Well Plate 200 µL
* Axygen 96 Deep Well Plate 2000 µL
* Eppendorf 96 Well Plate 200 µL
* [USA Scientific 12 Well Reservoir 22 mL #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [Opentrons 24 Well Aluminum Block with NEST 1.5 mL Screwcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis_part2/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis_part2/reagents.png)


### Protocol Steps
1. Make first mix.
2. Mixing and distribute first mix.
3. Pause for thermal cycling.
4. Distributing barcode.
5. Pooling samples.
6. Transfer beads to plate.
7. Incubating (hula step).
8. Remove supernatant.
9. Two ethanol washes.
10. Adding nuc free water.
11. Incubating (hula step).
12. Transfer to fresh well.
13. Make and add final mix.
14. Transfer beads to plate.
15. Incubating (hula step).
16. Removing supernatant.
17. Two washes.
18. Adding nuc free water.
19. Incubating (hula step).
20. Transfer to fresh well. 


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
onsite_egenesis_part2
