# SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB - Part 2

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Illumina Nextera Flex

## Description
This protocol is a semi-automated workflow which performs 8.1-8.4.6 of the SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB kit. For detailed information on protocol steps, please see below. You can find part 1 of the protocol here:

* [SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB - Part 1](https://protocols.opentrons.com/protocol/5b16ef)

Explanation of complex parameters below:
* `Number of Sample Columns (1-6)`: Specify how many sample columns (1-6) this run will process. Samples will be placed in every other column, starting from column 1 (i.e. 1, 3, 5, 7, 9, 11 for 6 columns).
* `csv`: csv should be formatted in the following order, including the header line (also be sure to skip columns):
```
Well, DNA Volume (ul), Pool Volume
A1, 5, 5
B1, 3, 5
C1, 5, 5
D1, 5, 5
E1, 2, 5
F1, 5, 5
G1, 5, 5
H1, 4, 5
A3, 5, 5
```
* `Index Start Column (1-12)`: Specify which column in the index plate to begin aspirating from. Note: the number of index columns left should be greater or equal to the number of sample columns. If not, the protocol will throw an error at the beginning of the run.
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 and P300 multi-channel pipettes.


---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 12 well reservoir 15mL](https://shop.opentrons.com/verified-labware/well-reservoirs/)
* [NEST 1 well reservoir 195mL](https://shop.opentrons.com/verified-labware/well-reservoirs/)
* Bio-Rad 96 Well Plate 200 µL PCR
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [Opentrons 20ul Tips](https://shop.opentrons.com/universal-filter-tips/)
* [Opentrons 300ul Tips](https://shop.opentrons.com/universal-filter-tips/)
* [NEST 12 well reservoir 195mL](https://shop.opentrons.com/verified-labware/well-reservoirs/)
* Index Plate

### Pipettes
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [Illumina DNA Prep](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

---

### Deck Setup
Note: Split the ethanol evenly in columns 11 and 12 of the reservoir if running 5 or 6 columns of samples. If running 4 or fewer columns of samples, place all the ethanol in column 11 of the reservoir exclusively.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b16ef/pt2/Screen+Shot+2022-04-14+at+1.48.51+PM.png)

### Reagent Setup

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b16ef/pt2/Screen+Shot+2022-04-14+at+1.49.23+PM.png)
![deepwell plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b16ef/pt2/Screen+Shot+2022-04-14+at+1.49.44+PM.png)
![deepwell plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b16ef/pt2/Screen+Shot+2022-04-14+at+1.50.01+PM.png)

---

### Protocol Steps
1. P20 multi-channel pipette picks up one tip to normalize DNA concentration in sample wells with water via csv. Water is first added to empty wells in the final plate on slot 4, and after, DNA from slot 1 is then added to the wells containing water. The samples in the plate on slot 4 mimic the plate on slot 1 (skipping every other column).
2. 20ul of tagment mastermix is added to samples and mixed 3 times.
3. Protocol pauses with message: "Seal plate with Microseal B. Using a thermal cycler with lid heated to 100C, incubate plate at 55C for 15 minutes, followed by 10C hold (step 11 of section 8.4.2 of protocol) Program "Flex Tag" on the thermal cycler. Afterwards, place plate back on slot 4 of the deck and select "Resume" on the Opentrons app for Post Tagmentation Cleanup. Empty trash if needed."
4. 10ul of TSB is added to samples. TSB is premixed, and mixed after dispensing into samples.
5. Protocol pauses with message: "Seal plate with Microseal A. Using a thermal cycler with lid heated to 100C, incubate plate at 37C for 15 minutes, followed by 10C hold (step 5 of section 8.4.3 of protocol). Program "Flex Post" on the thermal cycler. Afterwards, spin the plate, and place plate back on MAGNETIC MODULE and select "Resume" on the Opentrons app for washing. Empty trash if needed."
6. Magnets are engaged for 3 minutes, 60ul of supernatant removed from wells at half aspiration rate so as not to disturb the beads. Furthermore, aspirations take place on the side of the well opposite magnetically engaged beads to avoid disturbing the beads.
7. 3 Washes with 100ul of TWB, removing supernatant each time. On the last wash, TWB remains in wells to prevent bead drying.
8. Protocol pauses with message: "Ensure PCR mastermix is loaded onto the deck. Select "Resume" on the Opentron App. Empty trash if needed."
9. Supernatant is removed (TWB), 40ul of PCR mastermix is immediately added to samples and mixed.
10. Indexes are added to the samples. A set of tips are used to puncture the foil, dropped, new tips are granted, then the pipette aspirates 10ul of index to dispense into samples with 10 mix repetitions to follow.
11. Protocol pauses with the following message: "Seal the plate with Microseal A. Run the following preprogrammed settings on the thermal cycler with a headed lid (100C). Program "Flex Amp" on the thermal cycler. Ensure a fresh 96 well bio-rad plate is in slot 4 of the deck. Select "Resume" on the Opentron App. Empty trash if needed."
12. Magnetic module is engaged for 5 minutes.
13. 45ul of supernatant is removed from the sample plate to the 96 well plate on slot 4.
14. Protocol pauses with message: "Discard plate on magnetic module, and move plate from slot 4 to the magnetic module. Select "Resume" on the Opentron App. Empty trash if needed."
15. 81ul of SPB is added to samples. SPB is viscous, thus, the pipette will aspirate the SPB slowly, and then delay 3 seconds after aspirating 81ul to ensure that the liquid has enough time to draw. SPB is dispensed into samples, then mixed 10 times.
16. Samples are incubated at room temperature for 5 minutes.
17. 2 washes with Ethanol at 200ul.
18. Protocol delays for 5 minutes to allow beads to air dry, then automatically resumes.
19. 32ul of RSB is added to samples.
20. Samples incubate with RSB for 3 minutes. Magnets engage, then protocol delays for another 3.5 minutes.
21. Protocol pauses with message "Ensure a fresh 96 well bio-rad plate is in slot 4 of the deck. Select "Resume" on the Opentron App. Empty trash if needed."
22. 30ul of supernatant is removed and moved to slot 4, skipping every other column.
23. Samples are pooled with volumes provided by csv.


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
5b16ef-pt2
