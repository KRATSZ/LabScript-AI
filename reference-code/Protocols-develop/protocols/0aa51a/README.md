# PCR


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* Complete PCR Workflow


## Description
This protocol performs a PCR plating and PCR reaction on the Opentrons Thermocycler Module. The worklist input for where to transfer oligos should be specified in the following format, **including header line**:

```
Pipettor,Slot 5 well (Oligo source plate),Slot 10 well (Destination plate),Volume uL
P20 single channel,A6,A1,10
P20 single channel,C1,A1,10
P20 single channel,A1,B1,10
P20 single channel,A7,B1,2.5
P20 single channel,A8,B1,2.5
P20 single channel,A9,B1,2.5
...
```

You can download a template .csv file [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0aa51a/ex.csv).


### Modules
* [Opentrons Thermocycler Module](https://shop.opentrons.com/thermocycler-module-1/)


### Labware
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0aa51a/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0aa51a/reagents.png)


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
0aa51a
