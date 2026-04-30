# Cherrypicking


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Cherrypicking


## Description
This protocol performs a custom cherrypicking protocol for seeding up to 2 source plates to up to 2 destination plates. The input .csv file should be formatted as follows:

```
Original plate position in OT-2 workspace,Original position,Picking volume (ul),Destination plate position,Destination position,Seeding volume,Trashing volume,Cell medium original plate,Cell medium destination plate
1.1,B1,20,2.1,B1,20,0,40,40
1.1,B5,30,2.1,B2,20,10,30,40
1.1,C16,50,2.2,B1,30,20,10,30
1.2,B6,10,2.2,B2,10,0,50,50
1.2,D4,20,2.2,B3,10,10,40,50
1.2,E5,30,2.2,B4,20,10,30,40
...
```

You can also download a template file from [this link](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04552f/ex.csv).

To reflect the changes of your input .csv file, perform the following: paste the content of your .csv file as a multi-line string on line 17 of your download protocol, setting the variable `INPUT_CSV`.

### Labware
* [Corning 384 Well Plate 112 µL Flat #3640](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/384-Well-Microplates/Corning%C2%AE-384-well-Clear-Polystyrene-Microplates/p/corning384WellClearPolystyreneMicroplates)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04552f/deck.png)


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
04552f
