# Oxford Nanopore Rapid Barcoding with Normalization 


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Library Prep
	* Sequencing


## Description
This protocol automates steps 3-10 of the Oxford Nanopore Rapid Barcoding Kit [SQK-RBK110.96](file:///Users/parrishpayne/Downloads/rapid-barcoding-kit-96-sqk-rbk110-96-RBK_9126_v110_revO_24Mar2021-gridion%20(3).pdf). Choose between 16-32 samples per run (> 24 samples requires two 4-in-1 tube racks)


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* [Opentrons 96 Well Aluminum Block with Bio-Rad Well Plate 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 24 Well Aluminum Block with NEST 1.5 mL Screwcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9038af/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9038af/reagents.png)


### Protocol Steps
1. Transfer 50 ng genomic DNA per sample. Adjust the volume to 9 μl with nuclease-free water. Mix by pipetting.
2. Transfer 1 µL of the Rapid Barcodes to each sample. Mix by pipetting
3. Incubate the plate at 30°C for 2 minutes and then at 80°C for 2 minutes. Then cool the plate to 4°C on the temperature module.
4. Pool all barcoded samples, noting the total volume.
5. Resuspend the AMPure XP Beads (AXP, or SPRI) by vortexing.
6. To the entire pooled barcoded sample from Step 4, add an equal volume of resuspended AMPure XP Beads (AXP, or SPRI).
7. Mix by pipetting for 5 minutes at room temperature.

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
9038af
