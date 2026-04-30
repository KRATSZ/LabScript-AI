# Digestion and Bead Cleanup


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocols performs a blead cleanup on the OT-2 with overnight digestion step for 16, 32, or 48 samples. For detailed description of requirements and steps, please see below.

### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* TMTpro18 PCR strip plate #72.985.002
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [Opentrons 24 Tube Rack with Eppendorf 2 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0845ab/Screen+Shot+2023-12-10+at+9.35.34+PM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0845ab/Screen+Shot+2023-12-10+at+9.37.20+PM.png)


### Protocol Steps
1. 12 well reservoir (liquid stock plate) contains: A1= 100% ACN, A2= 70% ethanol
2. Eppendorf rack (liquid stock epps) contains: A1= bead solution, A2= 200 mM TEAB, A3= 5% HA, A4= 20% formic acid
3. Homogenize bead solution in A1 of Eppendorf rack (50 µl 3x, fast speed)
4. 4 µl beads from A1 to column 1-6* of slot 1 (same tips)
5. 30 µl of sample from column 1-6* slot 2 to column 1-6* slot 1 (A1 to A1, B2 to B2 etc, new tip always)
6. 70 µl of 100% ACN to column 1-6* of slot 1 (airgap, mix after every time, 3x low speed, new tip always)
7. Wait 2 mins
8. Engage magnetic module (magnetic beads as low as possible)
9. Wait 5 mins
10. Remove 100 µl from column 1-6* of slot 1, dispose in reservoir slot 11 (Consolidate, same tips)
11. Add 100 µl 70% ethanol to column 1-6* of slot 1 (one tip)
12. Remove 100 µl from column 1-6* of slot 1, dispose in reservoir slot 11 (Consolidate, same tips)
13. Repeat step 11-12
14. Disengage magnetic module
15. Wait 2 mins
16. Add 10 µl digestion solution to column 1-6* slot 1 (mix every time, 1x slowly, new tip always)
17. Pause protocol (‘move sample plate to heater shaker’)
18. Close HS module
19. Heater activate (37°C)
20. Pause protocol (‘Overnight digestion’)
21. Deactivate heater
22. Open HS module
23. Pause protocol (‘move sample plate to magnetic mod’)
24. Engage magnetic module (magnetic beads as low as possible)
25. Wait 2 mins
26. Move 10 µl from column 1-6* of slot 1 to new position in the same plate, according to the ‘sample transfer layout’ scheme attached (new tips always, low speed aspirate, away from mag beads, touch tip after dispense)
27. Add 5µl 200 mM TEAB to all TMT wells (new tip always, mix 3x)
28. Add 9 µl TMT/buffer mix from slot 9 to all samples**, according to the attached scheme ‘TMT layout’ (A1 -> A3, A5 or A7, B1 -> B3, B5 or B7 etc., new tip always, mix 3x low speed)
29. Wait 1 hr
30. Add 5 µl 5% HA to all samples** (new tip always, mix every time, 1x medium speed)
31. Wait 15 mins
32. Consolidate samples into one Eppendorf (B5-8 of slot 3), every two columns of samples combined into one epp (for triplos: column 7 + 8 from sample plate to B5 of slot 3, column 9 + 10 to B6 of slot 3, column 11 + 12 to B7, for monoplo: column 3 + 4 to B5)
33. Add 10 µl 20% formic acid to slots B5-8* of slot 3 (new tip always, mix after every time 3x high speed)


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
0845ab
