### Author
Michael Fichtner




## Categories
* DNA/RNA
	* DNA/RNA


## Description
This protocol will prepare and run a standard Endpoint-PCR with the opentrons Cycler Module (only tested with Gen1). It aims to provide sufficient flexibility in terms of sample and replicate numbers to avoid the need of multiple similar protocols.

Key benefits of the protocol are:
* The master mixes will be prepared in 50 ml falcons and all reagents and samples can be provided in 1.5 ml tubes.
* Thus, no manual pipetting steps are involved.
* Up to 12 different template samples can be used with up to 3 different master mixes.
* Only the p300 and p20 pipettes are needed.
* Needed volumes of the different reagents are calculated and shown in run tab.

Notes:
* A no-template control (NTC) will be automatically added for each master mix.
* The first well of every master mix will always be in row A. If the sample number + NTC is not a multiple of 8, the remaining wells of the last column will be left empty to have an easier plate layout.
* (e.g. You have 2 master mixes, 4 samples and 1 replicate each. The last well of master mix 1 will be E1 (NTC control). Master mix 2 will now be added to the wells A2 - E2, skipping the remaining wells of column 1. This is meant to make it less confusing down the road.)


### Modules
* [Opentrons Thermocycler Module](https://shop.opentrons.com/thermocycler-module-1/)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL
* [Opentrons 24 Well Aluminum Block with NEST 1.5 mL Screwcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Well Aluminum Block with NEST Well Plate 100 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
[deck](https://drive.google.com/open?id=1E1W92HHveoQJEblfzXOynKiVUMofAmA0)


### Reagent Setup
[reagents](https://drive.google.com/open?id=1vt3BBPGD7XKCplorlWHnOjGihgPvOTiU, https://drive.google.com/open?id=1Fx_SsQSPlXiwKEYsWtjFRVgN-vlHM7ci, https://drive.google.com/open?id=1ERF1CRX-2yoKkuyTm3ytyLM361joa1q7)


### Protocol Steps
1. Open the protocol and define the number of samples, replicates and master mixes. (Starting at line 140 of the script)
2. Open the protocol in the opentrons app. The exact volumes of the needed reagents are shown in the run tab.
3. (optional) The last required tip position of both boxes is shown at the end of the run tab.
4. Load the robot according to the deck layout. If less than 12 samples are run, the respective slots can be left empty. Same is true for the primer tubes and empty master mix tubes, if less than 3 master mixes are used.
5. Start run.
6. The robot will start to cool the cycler block and the temperature module to 4°C. Thus, it might take a while to start pipetting.
7. The robot will then prepare the master mixes and distribute it to the PCR plate.
8. Samples will be added to the plate.
9. All wells will be mixed.
10. The robot will run the pre-defined PCR.
11. Once finished, the cycler block will be cooled down to 4°C
12. (optional) If selected in the protocol, the robot will sort the remaining tips in the tip boxes to the front.
13. The PCR cycler will remain closed until opened manually.
14. Neither the temperature module nor the cycler module will be deactived to ensure all temperature sensitive reagents remain at 4°C until removed by the operator.



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
02pnzp
