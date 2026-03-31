# Automated RoboZooMS Protocol

### Author
[University of York BioArchaeology Team](https://www.york.ac.uk/archaeology/centres-facilities/bioarch/)



## Categories
* Sample Prep
	* Plate Filling

## Description
A start to finish protocol for preparation of archaeological bone samples for analysis by MALDI-TOF.
Currently configured for 12 or 24 samples, depending on the amount of eppendorf racks available.
Protocol can be adjusted for non-destructive analysis, and for NaOH wash to remove humic acids.

Samples are to be laid out left to right (A1 to A12), top to bottom (then B1 to B12).

The protocol is split into 5 main steps, with the first two being optional:

1. Hydrochloric acid demineralisation (optional)
2. Sodium hydroxide wash (optional)
3. Gelatine extraction
4. Trypsin digestion
5. Peptide extraction

---

### Labware
 * [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)
 * [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)
 	* This tube rack is optional however, it allows throughput to double from 12 to 24!
 * [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://labware.opentrons.com/opentrons_6_tuberack_falcon_50ml_conical?category=tubeRack)
 * [Opentrons 96 Tip Rack 1000 µL](https://labware.opentrons.com/opentrons_96_tiprack_1000ul?category=tipRack&manufacturer=Opentrons)
 * [Opentrons 96 Tip Rack 1000 µL](https://labware.opentrons.com/opentrons_96_tiprack_1000ul?category=tipRack&manufacturer=Opentrons)
 * [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack&manufacturer=Opentrons)
 * [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir&manufacturer=NEST)
 * [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate&manufacturer=Corning)

### Pipettes
 * P1000 Single GEN1
 * P300 Single GEN1

### Reagents
HCl and NaOH should be stored at 4°C prior to use.
 * 0.6 M Hydrochloric Acid (HCl)
 * 0.1 M Sodium Hydroxide (NaOH)
 * 50 mM Ammonium bicarbonate (AmBIC) buffer
 * 0.1% Trifluoroacetic acid (TFA) in ultrapure (UHQ) water (washing solution)
 * 0.1% TFA in 50:50 solution of UHQ water and acetonitrile (conditioning solution)
 * Trypsin solution (frozen and resuspended in 50 uL of re-suspension buffer as sold, as needed), made up to 10 mL with UHQ water

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/user-upload_ZooMS_Protocol/Deck_Setup.png)

Note that the 12 well reservoir in slot 11 is simply used as an aqueous waste (AqWaste) container.

* IMPORTANT:
 * If using one rack then the top two rows (A and B) are used for the "second extract" eppendorfs (where you place your sample to begin with) and bottom two rows are used for "Extract" exppendorfs (where the sample will be processed)
 * If using two racks then the top rack (default deck location: 8) is used to hold samples (labelled as SE) and the bottom rack (default deck location: 5) will hold the extracts (labelled EXT).

### Reagent Setup
![reagent layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/user-upload_ZooMS_Protocol/Reagent_Setup.png)

![well plate layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/user-upload_ZooMS_Protocol/Well_Setup.png)

---

### Protocol Steps
Note: volumes shown here are defaults which can be changed if needed.
Note: Manual steps indicated, followed by "automatically" when a robot takes over.

1. (optional) Add 250 uL of 0.6 M HCl from "falcon tube well 0" into the 1.5 mL eppendorf tubes containg 10-30 mg of bone (pause and manual resume here after demineralisation 1-14 days).
2. (optional) Remove acid from each eppendorf into AqWaste (reservoir trough 'A1'), add 250 uL 0.1 M of NaOH from "falcon tube well 2", manually vortex and centrifuge samples, then automatically remove NaOH from eppendorfs into AqWaste
3. Distribute 100 uL of 50 mM AmBIC into samples, manually incubate for 1 hr at 65°C then centrifuge 1 min and place samples back, automatically transfer 50 uL of gelatinized sample into EXT eppendorfs.
4. Distribute 1 uL of trypsin into EXT eppendorfs, mix, then manually incubate overnight at 37°C and place samples back, automatically add 50 uL of washing soltuion to quench trypsin.
5. Using a regular 1000 uL pipette: prepare the zip-tip wellplate by placing 250 uL of conditioning solution and 350 uL of washing solution into well plate as above
6. Using a filter-tip 300 uL pipette: slowly draw up conditioning solution twice (50 uL), wash the filter with washing solution twice (100 uL), draw sample (in EXT eppendorf) in and out 10 times, wash filter twice (100 uL), draw up conditioning solution (100 uL) and elute into third well, mixing 10 times (50 uL).

If not spotting directly, store eluted samples at -20 °C.


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.
