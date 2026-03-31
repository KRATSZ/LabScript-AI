# Illumina DNA Prep - Opentrons v3
### Author
[Opentrons](https://opentrons.com/)

### Partner
[Illumina](https://www.illumina.com/)



## Categories
* NGS Library Prep
	* Illumina DNA Prep

## Description
This protocol automates the [Illumina DNA prep protocol](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf). Illumina DNA prep offers a fast, integrated workflow for a wide range of applications, from human whole-genome sequencing to amplicons, plasmids, and microbial species

The protocol allows you to set the number of samples to 8, 16 or 24 (i.e. 8 samples per column, up to 3 columns). Samples are prepared in the wells as shown in the table and figure below, with 30 µL of 100 ng:s of sample DNA in each well. See the [Illumina DNA Prep protocol](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf) for more information about sample input requirements.

![Sample input and output columns](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-dna-prep/v3/samples_output.jpg)

![Sample columns](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-dna-prep/v3/sample_setup.jpg)

The user can choose which steps of the protocol they want to run, or skip - see explanation of parameters below.

**Plate Moving**
The Protocol requires manually transferring the sample plate between the Thermocycler and Magnet 3 times.  It starts on the Thermocycler and needs to be moved to the Magnet for the post-Tagmentation washes, and then moved to the Thermocycler for PCR and then back to the Magnet for the post-PCR cleanup.  In the script the two positions are handled as sample_plate_mag and sample_plate_thermo; during calibration use an empty plate of the same labware as the sample plate on the magnet position to allow calibration.

Explanation of parameters below:
* `Number of samples`: 8 (column 1), 16 (column 1, 3), or 24 (column 1, 3, 5) samples (see above).
* `Do a dry run?`: Sets the `Use modules?` parameter to `No` (see below). Tips will be returned, incubation steps skipped, and mixes shortened. This parameter is for testing purposes.
* `Use modules?`: Runs the protocol without module steps (e.g. thermocycle steps such as incubation and PCR cycles, or the steps using the magbetic module). Will be automatically set to `Yes` if the `Do a dry run?` parameter is set to `Yes`
* `Tip reuse?`: Reuses tips for washing steps so that no tip refill is neccesary during the run. Recommended only for a 24x samples run.
* `Use tip offsets?`: Whether to use specific offsets for each tip type
* `Include tagmentation step in protocol run?`: Run the tagmentation step or skip it.
* `Run tagmentation incubation on the deck thermocycler?`: Run the tagmentation incubation step on the deck thermocycler or on an off-deck external thermocycler.
* `Run TSB step?`: Run the TSB/adapter ligation step or not
* `Run TSB incubation step on the deck thermocycler`: Whether to do the incubation on the on-deck thermocycler or off-deck on an external thermocycler
* `Run tagmentation wash with TWB step`: Run the bead washing steps with TWB
* `Run PCR cycle step`: Whether to run the PCR amplification step
* `Run PCR step on deck thermocycler?`: Run the PCR amplification on the on-deck thermocycler or on an external thermocycler
* `Run post PCR cleanup step`: Run or skip the post-PCR bead cleanup using AMPure beads
---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [Nest 96 well plate full skirt 100 µL](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [NEST 2 mL 96-Well Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Opentrons aluminum block set](https://shop.opentrons.com/aluminum-block-set/)

### Pipettes
* [P300 multi-Channel (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 multi-Channel (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P10 multi-Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)
**Tips**
* [Opentrons 20 µL filter tiprack](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 200 µL filter tiprack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

### Reagents
* [Illumina DNA Prep](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-dna-prep/v3/deck.jpg)

Inital slot layout:
1. Magnetic module for the sample plate (Nest 96 well plate full skirt).
2. Reservoir: NEST 12-well reservoir 15 mL. This is substituted for a NEST 2 mL deep well plate if tip-reuse is on in order to minimize cross-contamination. See Reagent Setup section for information about the location of the reagents
3. Reagent plate 2: Temperature module with Bio-rad 200 µL plate on aluminum block. See Reagent Setup section for information about the location of the reagents
4. 20 µL filter tiprack
5. 200 µL filter tiprack
6. 200 µL filter tiprack
7. Sample plate on Thermocycler module with NEST 96 well plate full skirt 100 µL
8. Empty
9. 200 µL filter tiprack
10. Sample plate on Thermocycler module with NEST 96 well plate full (thermocycler uses two slots)
11. Empty

### Reagent Setup
* Reservoir, slot 2:
![Reagent plate 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-dna-prep/v3/reagent_plate1.jpg)
* Reagent plate on temperature module, slot 3:
![Reagent plate 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-dna-prep/v3/reagent_plate2.jpg)

---

### Protocol Steps
1. Prepare the thermocycler by setting the block temperature to 4 degrees, and the lid to 100 degrees.
2. Add tagmentation mix to the samples
3. User seals the plate and the protocol incubates the samples with the mix in the thermocycler, 55 degrees for 15 minutes.
4. The thermocycler opens, and the user removes the seal.
5. Add Tagmentation Stop Buffer to the samples.
6. Seal and incubate the mix at 37 degrees for 15 minutes.
7. User removes seal; remove the supernatant and wash the beads three times with Tagmentation Wash Buffer.
8. Amplification of DNA: Addition of PCR mix and addition of barcodes.
9. The protocol runs PCR protocol for 5 cycles. This takes 25 minutes to complete. The supernatant is transferred to columns 7, 9 and 11 depending on how many sample columns there are.
10. Post-PCR cleanup using AMPure beads.
11. The protocol performs two ethanol washes.
12. RSB (resuspension buffer) is added to the bead wells and the supernatant is transferred to the output columns (8, 10, and 12).

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
illumina-dna-prep
