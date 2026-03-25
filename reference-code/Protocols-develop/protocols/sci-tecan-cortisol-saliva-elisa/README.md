# Tecan Cortisol ELISA w/ Heater Shaker


### Author
Boren Lin




## Categories
* Proteins
	* Proteins


## Description
Tecan’s Cortisol Saliva ELISA (REF 30172091, Männedorf, Switzerland) is an enzyme immunoassay for the quantitative determination of free cortisol in human saliva. It is a competitive ELISA which the target antigen (free cortisol in specimen) competes with a reference antigen (fixed amount of HRP-labelled cortisol) for binding the anti-cortisol antibody pre-coated on the plate. A substrate for HRP is then added into the mixture to produce the photometric signal. The more the target antigen is present in the sample, the less the reference antigen can be captured by the antibody and the weaker the signal produced; therefore, the intensity of the developed color is inversely proportional to the amount of the target antigen in the sample.

The protocol performs transferring of the samples and reference antigen (Enzyme Conjugate) into the ELISA plate (Microtiter Plate, 8-well strips coated with rabbit anti-cortisol antibody) to allow the antibody to bind to the antigen. After a 2-hour incubation and washing, TMB Substrate Solution is transferred into the ELISA plate to develop photometric signal which can be measured on a microplate reader at 450 nm.

Materials provided in the kit:
1.	Rabbit anti-cortisol antibody coated microtiter plate (8-well strip x12)
2.	HRP-conjugated cortisol (Enzyme Conjugate)
3.	Cortisol Standards and Positive Controls
4.	TMB Substrate Solution 
5.	TMB Stop Solution
6.	Wash Buffer (10X)

Other materials required:
1.	Slit seal (BioChromato, Fujisawa, Japan)
2.	NEST 1 Well Reservoir 195 mL 
3.	NEST 96 Deep Well Plate 2mL
4.	Opentrons Tip Rack, 300 µL
5.	Nunc 96-Well Polypropylene Storage Microplates (Cat. #: 249947, Thermo Fisher, Waltham, MA, USA) or compatible 
6.	Microplate Reader

Pipettes and Modules
1.	Opentrons P300 8-Channel Pipette (GEN2)
2.	Heater Shaker Module (GEN1) with Aluminum Adaptor for 96-well Flat Plate

Deck setup:
Please see the deck layout as the general guideline for labware setup. 
1.	The ELISA plate is sealed with a slit seal and placed on the Heater Shaker Module (Slot 3). 
2.	Samples or sample dilutions are pre-loaded in the Nunc 96-Well Polypropylene Storage Microplates, the SAMPLES plate (Slot 1).
3.	The REAGENTS plate (Slot 4) is filled with Enzyme Conjugate in Column 1, TMB Substrate Solution in Column 2, and TMB Stop Solution in Column 3
Note: See Reagent Step for reagent plate preparation
4.	For WASH (Slot 5), sufficient wash buffer is filled in each well for 4 washes of 250 μL.
5.	Three boxes of Opentrons 96 tips (Slot 7, 10, and 11) are sufficient to run a full 96-well ELISA plate (12 8-well strips).  
6.	The WASTE plate is loaded at Slot 9.



### Labware
* Tecan ELISA 96-well on Heater Shaker #446469
* Thermo Scientific 96 Well Plate V Bottom 450 uL #249944/249946
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
[deck](https://drive.google.com/open?id=19lOAqOhCQwh45I_KiY92_RhT9Nj_6pUF)


### Reagent Setup
[reagents](https://drive.google.com/open?id=1wQArSR79MN3W-F-KhSabUd8IITuvk1Uj)


### Protocol Steps

1.	User is prompted to place the ELISA plate on the Heater Shaker Module, which is then secured when the latches close.
2.	The samples (50 μL per sample) are transferred into the ELISA plate.
3.	Enzyme Conjugate (100 μL per well) is added into the ELISA plate.
4.	The ELISA plate is agitated at 500 rpm for 120 min.
5.	The supernatant in each well is discarded.
6.	The wash buffer (250 μL per well) is added into the ELISA plate. 
7.	The supernatant in each well is discarded.
8.	For 3 more washes, Step 6 and 7 are repeated.
9.	Substrate Solution (100 μL per well) is added into the ELISA plate.
10.	The ELISA plate is agitated at 500 rpm for 30 min to develop photometric signal.
11.	Stop Solution (100 μL per well) is added into the EIA plate.
12.	The latches of the Heater Shaker Module open, and user is prompted to move the ELISA plate to a microplate reader.



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
sci-tecan-cortisol-saliva-elisa
