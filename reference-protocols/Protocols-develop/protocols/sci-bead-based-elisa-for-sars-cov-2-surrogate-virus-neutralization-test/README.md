# bead-based ELISA


### Author
Boren Lin




## Categories
* Proteins
	* Proteins


## Description
ACROBiosystems SARS-CoV-2 Spike RBD-coupled Magnetic Beads (Cat. #: MBS-K002, Newark, DE, USA) are streptavidin conjugated magnetic beads attached with biotinylated SARS-CoV-2 Spike RBD protein. Using RBD protein as the target antigen for neutralizing antibodies to bind, a bead-based ELISA is developed to detect anti-SARS-CoV-2 antibodies in serum samples. 

The protocol performs mixing and incubation of the RBD-conjugated magnetic beads with serum samples to enable specific binding of the RBD and neutralizing antibodies. The Magnetic Module renders magnetic separation of the beads from unbound molecules in the samples, which are removed by washing. Then, an HRP-conjugated anti-human IgG antibody is added. This antibody binds to neutralizing antibodies which are immobilized on the beads through the interaction with RBD. The complex formed on the beads is a typical format of a sandwich ELISA (antibody-antigen-antibody) which after another round of washes, can be exposed to a substrate of HRP to generate a photometric signal that can be measured on a microplate reader at 450 nm.

Reagents:
1.	SARS-CoV-2 Spike RBD-coupled Magnetic Beads (ACROBiosystems, Cat. #: MBS-K002, Newark, DE, USA)
2.	Mouse Monoclonal Anti-Human IgG Fc (HRP) (Abcam, Cat. #: ab99759, Cambridge, UK)
3.	Wash Buffer (20 mM Tris HCl, 130 mM NaCl, 0.05% Tween-20, pH 7.3)
4.	Dilution Buffer for sample or antibody preparation (20 mM Tris HCl, 130 mM NaCl, 0.05% Tween-20, 0.25% BSA pH 7.3)
5.	TMB Substrate Solution
6.	Stop Solution

Labware:
1.	Slit seal (BioChromato, Fujisawa, Japan)
2.	NEST 1 Well Reservoir 195 mL 
3.	NEST 96 Deep Well Plate 2mL
4.	Opentrons Tip Rack, 300 µL
5.	Corning 96 Well Plate 360 µL Flat or compatible 
6.	Microplate Reader

Pipettes and Modules
1.	Opentrons P300 8-Channel Pipette (GEN2)
2.	Heater Shaker Module (GEN1) with Aluminum Adaptor for 96-well Deep Well Plate
3.	Magnetic Moddule (GEN2)

Deck setup:
Please see the deck layout as the general guideline for labware setup. 
1.	The Heater Shaker Module is loaded at Slot 3. 
2.	Samples or sample dilutions are pre-loaded in a NEST 96 Deep Well Plate 2mL (the working plate) placed on the Magnetic Module (Slot 9)
3.	The REAGENTS plate (Slot 11) is filled with bead suspension in Column 1, Anti-Human IgG Antibody in Column 2, TMB Substrate Solution in Column 3, and Stop Solution in Column 4
Note: See Reagent Setup for reagent plate preparation
4.	For WASH (Slot 5), sufficient wash buffer is filled in each well for 6 washes of 250 μL.
5.	Three boxes of Opentrons 96 tips (Slot 3, 4, and 10) are sufficient to run a full plate of 96 samples.  
6.	The WASTE plate is loaded at Slot 6.
7.	A Corning 96 Well Plate 360 µL Flat (the FINAL plate) is loaded at Slot 7.



### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [Corning 96 Well Plate 360 µL Flat #3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
[deck](https://drive.google.com/open?id=1lEBa2fcXszBBB_ndEMUCY1tMzY6r2aJq)


### Reagent Setup
[reagents](https://drive.google.com/open?id=1U3BxMUJU47MGiUzZ56NvLjKUtdumpOiO)


### Protocol Steps

1.	User is prompted to place the working plate pre-loaded with samples (100 μL per sample) on the Magnetic Module.
2.	Bead suspension (20 μL per well) is transferred into the working plate.
3.	User is prompted to move the working plate to the Heater Shaker Module.
4.	The samples undergo a 60-min incubation at 1000 rpm.
5.	User is prompted to move the working plate to the Magnetic Module.
6.	The supernatant in each well is discarded while the magnet is engaged.
7.	The wash buffer (250 μL per well) is added into the working plate and mixed.
8.	The supernatant in each well is discarded while the magnet is engaged.
9.	For 2 more washes, Step 7 and 8 are repeated.
10.	Anti-Human IgG solution (100 μL per well) is added into the working plate.
11.	User is prompted to move the working plate to the Heater Shaker Module.
12.	The samples undergo a 60-min incubation at 1000 rpm.
13.	User is prompted to move the working plate to the Magnetic Module.
14.	The supernatant in each well is discarded while the magnet is engaged.
15.	The wash buffer (250 μL per well) is added into the working plate and mixed.
16.	The supernatant in each well is discarded while the magnet is engaged.
17.	For 2 more washes, Step 15 and 16 are repeated.
18.	TMB Substrate Solution (100 μL per well) is added into the working plate.
19.	User is prompted to move the working plate to the Heater Shaker Module.
20.	The samples undergo a 5-min incubation at 1000 rpm.
21.	User is prompted to move the working plate to the Magnetic Module.
22.	Stop Solution (50 μL per well) is added into the working plate.
23.	The supernatant (100 μL per well) in each well is transferred to the FINAL plate while the magnet is engaged.
24.	User is prompted to move the FINAL plate to a microplate reader.



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
sci-bead-based-elisa-for-sars-cov-2-surrogate-virus-neutralization-test
