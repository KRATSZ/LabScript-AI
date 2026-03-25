# Thermocycler 4Plates 384PCR 12PrimesSets-32cDNAsQuad


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol preps (4) 384 well plates with a source plate on the Thermocycler module. For a detailed description of protocol steps, please see below. Gantry speed slowed to retard dripping.


### Modules
* [Opentrons Thermocycler Module](https://shop.opentrons.com/thermocycler-module-1/)


### Labware
* Applied Biosystems (ThermoFisher/Life) 4309849 With Barcode 384 Well Plate 30 µL 
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/036016/Screen+Shot+2022-12-23+at+10.22.07+AM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/036016/Screen+Shot+2022-12-23+at+10.23.26+AM.png)


### Protocol Steps
1. Set Thermocycler Block to 4C and Lid to 40C while closed.
2. Using P20 8-Channel Gen 2
Transfer 10ul from Sector 9: Corning 96 Well Plate 360ul Flat Column 1, Rows A-H (All Rows),
to Sector 5: Custom 384 Well PCR Plate, Columns 1-8, Rows A-P (All Rows) ● Once at Start of Step Sterility Multi Dispense
● Aspirate and Dispense Flow Rate 2ul/s
● Aspirate and Dispense Tip Position 0.5mm
● Delay 1s at 0.5mm on Aspirate, Delay 1s at 1.5mm on Dispense ● No Disposal Volume
● Well Order Top to Bottom then Left to Right
● Slow Gantry Speed to 50% speed when moving between Sectors ● Slow Gantry speed to 25% speed when moving within a Sector 3. Repeat Step 2 exactly except,
Transfer 10ul from Sector 9, Column 2, Rows A-H (All Rows), to Sector 5 Columns 9-16, Rows A-P (All Rows)
4. Repeat Step 2 exactly except,
Transfer 10ul from Sector 9, Column 3, Rows A-H (All Rows), to Sector 5 Columns 17-24, Rows A-P (All Rows)
5. Repeat Steps 2,3,4, exactly except,
Transfer 10ul from Sector 9, Columns 4,5,6 to Sector 6 Columns 1-8, 9-16, 17-24
6. Repeat Steps 2,3,4 exactly except,
Transfer 10ul from Sector 9, Columns 7,8,9 to Sector 2 Columns 1-8, 9-16, 17-24
7. Repeat Steps 2,3,4 exactly except,
Transfer 10ul from Sector 9, Columns 10,11,12 to Sector 3 Columns 1-8, 9-16, 17-24
8. Open Thermocycler.
9. Using P20 8-Channel Gen 2
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 1, Rows A-H (All Rows), to
Sector 5, Columns 1,2,9,10,17,18, Rows A-P (All Rows)
● Once at Start of Step Sterility Multi Dispense
● Aspirate Flow Rate 2ul/s, Dispense Flow Rate 0.2ul/s
● Aspirate Tip Position 1mm, Dispense Tip Position 0.5mm ● Delay 1s at 0.5mm on Aspirate, Delay 1s at 1.5mm on Dispense ● 1ul Disposal Volume, Blowout Trash
● Well Order Top to Bottom then Left to Right
● Slow Gantry Speed to 50% speed when moving between Sectors ● Slow Gantry speed to 25% speed when moving within a Sector 10.Repeat Step 9 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 1, Rows A-H (All Rows), to
Sector 6, Columns 1,2,9,10,17,18, Rows A-P (All Rows)
● Never Change Tip
11. Repeat Step 9 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 1, Rows A-H (All Rows), to
Sector 2, Columns 1,2,9,10,17,18, Rows A-P (All Rows)
● Never Change Tip
12.Repeat Step 9 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 1, Rows A-H (All Rows), to
Sector 3, Columns 1,2,9,10,17,18, Rows A-P (All Rows)
● Never Change Tip
13.Repeat Steps 9,10,11,12 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 2, Rows A-H (All Rows), to
Sectors 5,6,2,3 Columns 3,4,11,12,19,20 Rows A-P (All Rows) 14.Repeat Steps 9,10,11,12 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 3, Rows A-H (All Rows), to
Sectors 5,6,2,3 Columns 5,6,13,14,21,22 Rows A-P (All Rows) 15.Repeat Steps 9,10,11,12 exactly except,
Transfer 1ul from In Thermocycler: Nest 96 Well Plate 100ul PCR Full Skirt, Column 4, Rows A-H (All Rows), to
Sectors 5,6,2,3 Columns 7,8,15,16,23,24 Rows A-P (All Rows)


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.



### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
036016
