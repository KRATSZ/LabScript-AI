# NEBNext Ultra II Directional RNA Library Prep Kit for Illumina Part 2: RNA Isolation


### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext® Ultra™ II Directional RNA Library Prep


## Description
This protocol is part 2 of a 10 part series. Please look at deck map and liquid legend below. Note: bead strip tubes can accommodate 2 columns of sample by volume (i.e. 6 columns of beads for a full plate of samples). The RNA binding buffer can accommodate 3 columns of sample per column of wash. There only needs to be one column of strand primer mix per run for all sample numbers. An overage of at least 10% should be used each run.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* [Armadillo 96 Well Plate 200 µL PCR](https://labware.opentrons.com/armadillo_96_wellplate_200ul_pcr_full_skirt?category=wellPlate)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* Opentrons 96 Filter Tip Rack 200 µL
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00f7b1/Part+2/new+deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00f7b1/Part+2/Screen+Shot+2022-11-23+at+10.44.42+AM.png)


### Protocol Steps
1. Beads added to sample and mixed
2. Protocol pause
3. Samples mixed
4. Magnet engaged, supernatant removed
5. Beads washed twice with buffer
6. Supernatant removed
7. Tris added to sample
8. Protocol pause
9. Binding buffer added to sample
10. Incubate 5 minutes
11. Magnet module engaged
12. Supernatant removed
13. Final wash
14. Remove supernatant
15. Master mix elution added to sample
16. Protocol pause
17. Incubation
18. Moving RNA to new plate


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
00f7b1_part2
