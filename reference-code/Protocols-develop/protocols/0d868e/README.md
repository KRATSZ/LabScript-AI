# Ilumina TruSeq Stranded mRNA - Part 1

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Generic


## Description
This protocol performs sections 1 & 2 of the Ilumina TruSeq Stranded mRNA SOP (Purify mRNA to the end of Fragment mRNA). Pauses are included in the protocol for user intervention. Pauses will include details from the SOP for the user to follow for manual steps - the user may see these details in the Opentrons App during the pause. In the event of tip depletion, the protocol will automatically pause prompting the user to refill tips. Magnetic engagement height should be determined and adjusted accordingly, since the plate on the magnetic module is not in the labware library. If reagents take more than one column in the reagent plate (BWB for example), then the reagent volume in each well should be per sample, otherwise, reagent liquid volume should be per protocol if reagent takes one column.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Froggabio 96 Well Plate 300 µL
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt1/Screen+Shot+2022-12-12+at+4.09.37+PM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt1/Screen+Shot+2022-12-12+at+4.10.20+PM.png)
![reagents2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt1/Screen+Shot+2022-12-12+at+4.10.11+PM.png)


### Protocol Steps
1. This protocol performs sections 1 & 2 of the SOP (Purify mRNA to the end of Fragment mRNA).


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
0d868e
