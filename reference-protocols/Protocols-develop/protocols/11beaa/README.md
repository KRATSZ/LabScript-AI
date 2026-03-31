# qPCR Prep with 384 Well Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 384 well BIO-RAD plate for PCR. The protocol can be considered in 3 main parts:

* cDNA is added to the SuperMix and mixed
* Resulting solution (mastermix) is added to each well in the 384 well PCR plate
* Primer is added to each well in the 384 well plate

Since this protocol relies on the transfer of small amounts of liquid (in some cases 1ul transfers), aspiration and dispense flow rates are slowed, as well as incorporating blowout steps and proper aspiration/dispense heights to ensure proper distribution.

Explanation of complex parameters below:

* `Number of Samples`: Specify the number of primer pairs you will be running in this run (1-12, and wholly divisible by 2). A value of 2 will provide enough primer for 4 columns on the 384 well PCR plate, a value of 4 will accommodate 8 columns, and so forth.
* `cDNA Column`: Specify which columns the cDNA will be hosted in Slot 4 of the deck. Select `0` for column 2 if only running one cDNA column.
* `Aspiration height from well bottom`: Specify (in mm) the distance above the well bottom all aspirations steps will aspirate from.
* `Dispense height from well bottom`: Specify (in mm) the distance above the well bottom all dispense steps will dispense from.
* `Aspiration flow rate for P10-Multi (ul/sec)`: Specify the aspiration flow rate for the P10-Multi.
* `Aspiration flow rate for P50-Multi (ul/sec)`: Specify the aspiration flow rate for the P50-Multi.
* `Dispense flow rate for P10-Multi (ul/sec)`: Specify the dispense flow rate for the P10-Multi.
* `Dispense flow rate for P50-Multi (ul/sec)`: Specify the dispense flow rate for the P50-Multi.
* `Use Temperature Module`: If `Yes` is selected, the temperature module will be engaged over the course of the protocol with the user-specified temperature. A selection of `No` disengages the temperature module over the course of the protocol.
* `Temperature Module Temperature`: Specify the temperature the temperature module will hold over the duration of the protocol if `Yes` is selected in the `Use Temperature Module` parameter.
* `Small Volume Pipette`: Specify where a GEN1 or GEN2 pipette will be employed.
* `Large Volume Pipette`: Specify where a GEN1 or GEN2 pipette will be employed.
* `P10-Multi mount`: Specify which side the P10-Multi pipette will be mounted.
* `P50-Multi mount`: Specify which side the P10-Multi pipette will be mounted.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)


### Labware
* PerkinElmer Deepwell Pro Plate 96V 450µL (cat 6008299)
* BIO-RAD #HSP3865: Hard-Shell 384-Well PCR Plate, thin wall, skirted.
* BIO-RAD #HSP9601: HardShell 96Well PCR Plates, low profile, thin wall, skirted



### Pipettes
* Opentrons P10_Multi Channel Pipette
* Opentrons P50_Multi Channel Pipette


### Reagents
* Cell-cultures are grown in 96w plates.

* RNA isolation: SV 96 Total RNA Isolation System (Promega #Z3505)
cDNA synthesis: iScript Reverse Transcription Supermix for RT-qPCR (BIO-RAD # 1708840/1. This step is performed in a Vol of 40 µL/reaction. Of these 30µL of cDNA is applied to 270 µL (SuperMix+Water) => 300µL MasterMix to provide enough for 24x 10µL/well on the 384w qPCR-plate.
qPCR: [IQ SYBR Green Supermix (BIO-RAD #170-8884)](https://www.bio-rad.com/webroot/web/pdf/lsr/literature/10016680.pdf)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11beaa/Screen+Shot+2021-05-12+at+2.33.53+PM.png)

### Reagent Setup
* SuperMix on slot 1:
![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11beaa/Screen+Shot+2021-04-21+at+4.37.32+PM.png)
* PrimerPairs on slot 3:
![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11beaa/Screen+Shot+2021-04-21+at+4.37.16+PM.png)
* cDNA on slot 4. Note: cDNA can be in any two columns specified in the customizable parameters.
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/11beaa/Screen+Shot+2021-04-21+at+4.36.40+PM.png)


---

### Protocol Steps
1. cDNA from the first user-specified column is transferred to  Supermix in column 1, slot 1.
2. The resulting Mastermix is then distributed to rows (A, C, E, G, I, K, M, O) four columns at a time. This step is repeated until all aforementioned rows are populated across the entire 24 column tray.
3. cDNA is then transferred from the other user-specified column and is transferred to the Supermix in column 2, slot 2.
4. Step (2) is repeated but with rows (B, D, F, H, J, L, N, P). 384 well plate is completely populated with mastermix after this step if running full primer pairs.
5. PrimerPairs from each column in slot 3 are distributed to two columns on the 384 well PCR plate in slot 2 by row (A, C, E, G, I, K, M, O), and then (B, D, F, H, J, L, N, P). This allows for each reaction to be run in duplicates on the PCR plate.


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
11beaa
