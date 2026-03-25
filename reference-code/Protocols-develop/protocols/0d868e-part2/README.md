# Ilumina TruSeq Stranded mRNA - Part 2

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Generic


## Description
This protocol performs sections 3 to 8 of the Ilumina TruSeq Stranded mRNA SOP (Synthesize First Strand cDNA to the end of Cleanup Ligated Fragments). Pauses are included in the protocol for user intervention. Pauses will include details from the SOP for the user to follow for manual steps - the user may see these details in the Opentrons App during the pause. In the event of tip depletion, the protocol will automatically pause prompting the user to refill tips. Magnetic engagement height should be determined and adjusted accordingly, since the plate on the magnetic module is not in the labware library. If reagents take more than one column in the reagent plate (beads for example), then the reagent volume in each well should be per sample, otherwise, reagent liquid volume should be per protocol if reagent takes one column.


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Froggabio 96 Well Plate 300 µL
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons 24 Well Aluminum Block with NEST 2 mL Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.45.31+PM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.45.31+PM.png)
![reagents2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.46.17+PM.png)
![reagents3](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.46.30+PM.png)
![reagents4](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.46.42+PM.png)
![reagents5](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0d868e/pt2/Screen+Shot+2022-12-12+at+5.46.55+PM.png)


### Protocol Steps
1. This protocol performs sections 3 to 8 of the SOP (Synthesize First Strand cDNA to the end of Cleanup Ligated Fragments).


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
0d868e-part2
