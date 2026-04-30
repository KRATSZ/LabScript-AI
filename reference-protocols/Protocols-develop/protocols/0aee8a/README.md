# Combo IC-50 (Serial Dilution of Compounds)


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Serial Dilution


## Description
This protocol outlines serial dilution of compound stock. There is an optional predilution step for each compounds involved. For detailed protocol steps, please see below. Labware setup consists of NEST 12 well 15mL reservoir in slot 1, Nest 96 well 100 uL plate in slot 2,4,5,7,8,10 & 11 as well as P20 filter tips in slot 3 and P200 filter tips in slot 6.


### Labware
* [Opentrons 200ul Filter Tips ](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [NEST 12-Well Reservoirs 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup

Volume Definitions:
* VOL1= DMSO transfer volume for vertical plates (post dilution volume) 
* VOL2= DMSO transfer volume for horizontal plates (post dilution volume)
* VOL3= Compound C predilution volume DMSO (optional)
* VOL4= Compound D predilution volume DMSO (optional)
* VOL5= Compound A predilution volume DMSO (optional)
* VOL6= Compound B predilution volume DMSO (optional)
* VOL7= Compound C predilution volume compound (optional)
* VOL8= Compound D predilution volume compound (optional)
* VOL9= Compound A predilution volume compound (optional)
* VOL10= Compound B predilution volume compound (optional)
* VOL11= Compound C/D initial volume 
* VOL12= Compound C/D Serial dilution volume 
* VOL13= Compound A/B initial volume
* VOL14= Compound A/B serial dilution volume
* VOL15= Final plate volume for integra transfer 

### Protocol Steps

1.	Using p300, transfer VOL1 ul from the DMSO reservoir in slot 1 into B-H 1/12 in slot 7 (Vertical stamp plate) keep tip
2.	Using p300, transfer VOL2 uL from the DMSO reservoir in slot 1 into A2-12/H2-12 in slot 8 (Horizontal stamp plate) dispose tip
3.	(Steps 3-6 are optional) Using p300/20, transfer VOL3/4 from the DMSO reservoir to A2/11 in slot 7 
4.	Using p300/20, transfer VOL5/6 from the DMSO reservoir to B1/G1 in slot 8 
5.	Using p300/20, transfer VOL7/8 from well B1/B2 slot 2 (compounds C/D) into A2/11 in slot 7, using new tips
6.	Using p300/20, transfer VOL9/10 from well A1/A2 from slot 2 (compounds A/B) into B1/G1 in slot 8, new tips
7.	Using p300, transfer VOL11 from well B1 slot 2 or well A2 slot 7 (if optional predilution was done) to A1 slot 7, mixing before, keep tip
8.	Using p300, transfer VOL12 from well A1 to well B1, mix after, keep tip
9.	Repeat from B1-C1 C1-D1 … F1-G1 d tip
10.	Using p300, transfer VOL11 from well B2 slot 2 or well A11 slot 7 (if optional predilution was done) to A12 slot 7, mixing before, keep tip
11.	Using p300, transfer VOL12 from well A12 to well B12, mix after, keep tip
12.	Repeat from B12-C12 C12-D12 … F12-G12 dispose tip
13.	Using p300, transfer VOL13 from well A1 slot 2 or well B1 slot 8 (if optional predilution was done) to A1 slot 8, mixing before, keep tip
14.	Using p300, transfer VOL14 from well A1 to well A2, mix after, keep tip
15.	Repeat from A2-A3 A3-A4 … A10-A11 dispose tip
16.	Using p300, transfer VOL13 from well A2 slot 2 or well G1 slot 8 (if optional predilution was done) to H1 slot 8, mixing before, keep tip
17.	Using p300, transfer VOL14 from well H1 to well H2, mix after, keep tip 
18.	Repeat from H2-H3 H3-H4 … H10-H11 dispose tip
19.	Using p20, transfer VOL15 from well H1 slot 7 to wells H1-12 slot 10, blowout after, keep tip
20.	Repeat for rows G-A col 1
21.	Using p20, transfer VOL15 from well H12 slot 7 to wells H1-12 slot 11, blowout after, keep tip
22.	Repeat for rows G-A col 12
23.	Using p20, transfer VOL15 from well A12 slot 8 to wells A12-H12 slot 4, blowout after, keep tip
24.	Repeat for row A cols 11-1 
25.	Using p20, transfer VOL15 from well H12 slot 8 to wells A12-H12 slot 5, blowout after, keep tip
26.	Repeat for row H cols 11-1 


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
0aee8a
