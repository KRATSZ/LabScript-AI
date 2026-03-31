# Bacterial Plating and Dilution


### Author
Lachlan Munro




## Categories
* Microbiology
	* Microbiology


## Description
This is a protocol to dilute and spot bacteria for isolation and quantification. Bacterial samples are passed through 10, 10x serial dilutions with each dilution spotted onto agar. This can process up to 40 samples at a time (5 plates x 8 wells (1 column) per plate). 

Plates should be preloaded with the bacterial samples in column 1 and 90 µL of dilution buffer or media in columns 2-12. Agar plates should be prepared by filling Nunc Omnitrays with 30 mL of melted agar. These should be dried on as flat a surface as possible to ensure consistent heights across the plate.

Calibration on the agar plate should be performed so that the tips are just barely touching the agar as the "top of the well". 


### Labware
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
[deck](![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/33y0f3/deck.png))


### Reagent Setup
[reagents](![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/33y0f3/reagents.png))


### Protocol Steps
For each plate that is present the protocol 
1. Takes 5 µL of bacterial sample and spots it onto the agar plate. 
2. transfers 10 µL of sample to the next column and mixes 
3. Returns to step 1, taking from the newly diluted column
4. Continues until 10 serial dilutions have been performed.
5. Takes clean tips and repeats for the next plate.


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
33y0f3
