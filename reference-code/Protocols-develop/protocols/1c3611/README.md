# 384-Well PCR Prep


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep


## Description
This protocol performs a custom 384-well PCR preparation. The user has the option to enter the following parameters:
* number of samples
* volume of sample
* number of mastermixes
* volume of mastermix
* number of replicates per sample + mastermix combination

Mastermixes should be pre-mixed and loaded into individual tubes as shown below. For efficiency, the mastermixes will first be plated from their source tubes into distribution columns using a single channel pipette, before being loaded into the 384-well plate with an 8-channel pipette.

For sample traceability, an output .csv file will be written to the robot's Jupyter notebook server for each protocol run. The user has the option to input a `run ID` to distinguish each run. To find these output files, please refer to [this support article](https://support.opentrons.com/s/article/Uploading-files-through-Jupyter-Notebook).


### Labware
* [Opentrons 24 Tube Rack with Eppendorf 2 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Corning 384 Well Plate 112 µL Flat #3640](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/384-Well-Microplates/Corning%C2%AE-384-well-Clear-Polystyrene-Microplates/p/corning384WellClearPolystyreneMicroplates)
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1c3611/deck2.png)


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
1c3611
