# Nanoporo Direct RNA Sequencing


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
For a detailed description of this protocol, please refer to the [Nanoporo Direct RNA sequencing (SQK-RNA002) SOP](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis/direct-rna-sequencing-sqk-rna002-DRS_9080_v2_revO_14Aug2019-minion+(2).pdf).

Note: wash buffer should be split evenly between wells A5 and A6 on slot 5.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Eppendorf 96 Well Plate 200 µL
* [USA Scientific 12 Well Reservoir 22 mL #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [Opentrons 24 Well Aluminum Block with NEST 1.5 mL Screwcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis/dkdkdkdk.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_egenesis/reagents.png)


### Protocol Steps
1. Make mix 1.
2. Distribute mix to RNA tubes.
3. Make mix 2.
4. Distribute to rna tubes.
5. Add reverse transcriptase.
6. Transfer sample to plate.
7. Pause for user to thermocycle sample plate.
8. Transfer beads to plate.
9. Mix samples, aspirate sample into tip, incubate at top of the well for 1 minutes, repeat 4 times.
10. Remove supernatant.
11. Add ethanol to samples.
12. Remove supernatant.
13. Add nuclease free water.
14. Transfer to fresh column (column 3).
15. Make and distribute 3rd mix.
16. Transfer beads to plate.
17. Remove supernatant.
18. Add wash buffer.


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
onsite_egenesis
