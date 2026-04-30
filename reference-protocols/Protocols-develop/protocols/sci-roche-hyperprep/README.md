# Roche HyperPrep

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* NGS Library Prep
	* Roche HyperPrep

## Description
In the script there is a setting definition for the number of samples (SAMPLES = 8x, 16x, or 24x).  Samples are prepared as below, with 50ul of 100ng of fragmented sample DNA.  See the Roche/KAPA HyperPrep protocol for more information about sample input requirements.
* ![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/1.png)

* Plate Moving
The Protocol requires manually transferring the sample plate between the Thermocycler and Magnet 3 times.  It starts on the Thermocycler and needs to be moved to the Magnet for the post-ligation cleanup, and then moved to the Thermocycler for PCR and then back to the Magnet for the post-PCR cleanup.  In the script the two positions are handled as sample_plate_mag and sample_plate_thermo; during calibration use an empty plate of the same labware as the sample plate on the magnet position to allow calibration.

* Tip Tracking
Tip Tracking is an option meant to reuse tips for repeated washes.  Instead of discarding tips the OT2 will replace them in their original location for repeated use, this reduces the number of tips needed and allows a 24 sample run to require no tiprack replacements.  To prevent cross contamination when reusing Tips, when running the protocol with tip reuse, the reservoir is a 96x 2ml deepwell plate instead of a 12x well 15ml plate.  See Reservoir for more details.
* ![tips](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/tips.png)


Explanation of complex parameters below:
* `Number of Samples`: Specify number of samples 8, 16, or 24.
* `Dry Run`: Specify whether performing a dry run or not.
* `Modules or no modules`: YES or NO, 'YES' will not require modules on the deck and will skip module steps, for testing purposes, if DRY RUN is 'YES', then NO MODULES will automatically set itself to 'NO'
* `Reuse tips`: YES or NO, Reusing tips on wash steps reduces tips needed, no tip refill needed, suggested only for 24x run with all steps

* `Offset`: YES or NO, Sets whether to use protocol specific z offsets for each tip and labware or no offsets aside from defaults
* `Include ERAT`: Steps with "DECK" are for reaction to take place with the on deck Thermocycler module. This arrangement makes it possibly to set up and run only the first half, or to skips steps and resume if there is an Error.
* `Include ERAT Deck step`: If non "DECK" steps are skipped, then TIPREUSE will automatically set
itself to 'NO' in order to keep tip order correct.



---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)


### Labware
* NEST 12 Well Reservoir 195mL
* Eppendorf 96 well plate full skirt
* Nest 96 well plate full skirt
* Opentrons 20ul Filter Tips
* Opentrons 200ul Filter Tips

### Pipettes
* Opentrons P300 Multi-Channel Pipette GEN2
* Opentrons P20 Multi-Channel Pipette GEN2
* Opentrons P300 Multi-Channel Pipette GEN1
* Opentrons P10 Multi-Channel Pipette GEN1


### Reagents
* [kit name when applicable](link to kit)
* Nick is working on auto-filling these sections from the protocol (3/28/2021)

---

### Deck Setup
* ![decksetup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/Screen+Shot+2022-02-18+at+4.26.51+PM.png)
* Position 1	Magnetic Module
* Position 2	Reservoir
* Position 3	Temperature Module w/ Reagent Plate
* Position 4	p20
* Position 5	p300
* Position 6	p300
* Position 7	Thermocycler Module w/ Sample Plate
* Position 9	p300

* Reservoir w/o Tip Reusing
* ![reuse](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/with+reuse.png)
* Reservoir w/ Tip Reusing
* ![reuse](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/without+reuse.png)

### Reagent Setup
* Reagent Plate
Prepare the reagents in the Reagent Plate according to the table below.  If available, prepare extra volume according to the HyperPrep kit being used (24x or 96x).  

* ![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/Screen+Shot+2022-02-18+at+4.20.57+PM.png)
* Barcodes
Based on a quantified input of 100ng of fragged DNA, we suggest the KAPA Unique Dual-Indexed Adapter Kit (15 μM) with an adapter ratio 7.5uM.  Using the KAPA Adapter Diluent, add 3ul to column 7, 8, and 9 depending on how many samples are being run.  Add 3ul of the appropriate adapter to column 7, 8, and 9 according to the experiment design.  See KAPA HyperPrepKit instructions for further details.  
* ![barcodes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-roche-hyperprep/Screen+Shot+2022-02-18+at+4.18.52+PM.png)

---

### Protocol Steps
1. This section should consist of a numerical outline of the protocol steps, somewhat analogous to the steps outlined by the user in their custom protocol submission.
2. example step: Samples are transferred from the source tuberacks on slots 1-2 to the PCR plate on slot 3, down columns and then across rows.
3. example step: Waste is removed from each sample on the magnetic module, ensuring the bead pellets are not contacted by the pipette tips.

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
sci-roche-hyperprep
