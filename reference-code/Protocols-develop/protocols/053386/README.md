# Human Islets - Preprocessing


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
For detailed protocol steps, please see below. The trash will be used as a waste reservoir for supernatant removal. This protocol is for full plates (96 samples) exclusively. The protocol will pause to prompt the user to replace tips when needed, and pause for certain centrifuging steps.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/053386/reagents.png)


### Protocol Steps
1. Manually picked 1 islet per well into a 96-well plate with 100 μl of PBS pre-added into each well.
2. Spin down the plate at 200g for 5 min.
3. Pipette out 80 μl of supernatant.
4. Add 100 μl of pre-warmed 0.05% Trypsin into each well.
5. Digest the islets for 9 min at 37oC thermo incubator.
6. Pipette trituration with a volume of 80 μl 12 times towards the end of incubation.  
7. Stop the digestion by adding 100 μl of PBS+10%FBS into each well. Pipette mix.
8. Spin down the plate at 400g for 5 min.
9. 1. Pipette out 150 μl of supernatant.
10. Wash once with 100 μl of PBS+10%FBS/well. Pipette mix.
11. Spin down the plate at 400g for 5 min.
12. Pipette out 100 μl of supernatant.
13. Add 100 μl of cold methanol into each well. Incubate at -20oC for 10 min.
14. Spin down the plate at 800g for 5 min at 4oC.
15. Pipette out 100 μl of supernatant.
16. Wash cells with 200 μl of wash-resuspension buffer (3xSSC+0.5 %BSA+0.2U/μl RNase inhibitor + 1mM DTT). Pipette mix 3x.
17. Pellet cells at 800g for 6 min.
18. Aspirate and discard 180 μl of supernatant



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
053386
