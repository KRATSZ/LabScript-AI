# Ilumina DNA Prep Part 2 - Post Tagmentation Cleanup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina DNA Prep

## Description
This protocol is part 2 of a 3 part series which preps a 96 well Bio-Rad 200ul plate in accordance with the [Ilumina DNA Prep Kit](https://emea.support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf).

* [Part 1: Tagment DNA](https://protocols.opentrons.com/protocol/0bf4f4)
* [Part 3: Cleanup libraries](https://protocols.opentrons.com/protocol/0bf4f4-pt3)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples for this run.
* `Index start column`: Specify which column to start aspirating from on the index plate.
* `P300 tip start column on slot 11 (1-12)`: The number of columns of tips used on slot 11 is equal to the number of columns of samples. Slot 11 tip rack is used for tip parking on the two ethanol washes to save tips. Specify which column to start picking tips up from.
* `Length from side`: Specify the length from the side of the well to aspirate from magnetically engaged beads. A value of 1 would be 1mm from the side of the well opposite beads. A value of 2.73 means the exact center of the well. This distance is also used when re-suspending beads, and mixing at bead location.
* `Aspiration height`: Specify how many millimeters from the bottom of the well to aspirate from at the `Length from side` distance specified above.
* `P20 Multi-Channel GEN2 Mount`: Specify which side (left or right) the P20 multi channel pipette is mounted.
* `P300 Multi Channel GEN2 Mount`: Specify which side (left or right) the P300 multi channel pipette is mounted.


### Labware
* [Bio-RAD 96 well plate 200ul](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Nest 12 Well Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20ul Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Opentrons 200ul Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P20 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Ilumina DNA Prep](https://emea.support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf)

---

### Deck Setup

* Deck setup with a full plate of samples. Tip rack on slot 11 will be used to park tips in ethanol wash steps.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt2/Screen+Shot+2021-07-16+at+12.46.50+PM.png)

### Reagent Setup

* Reagent Plate on Slot 2. EPM doesn't have to be added until a pause in the protocol. Note: liquid waste will be disposed of in column 12 of the reservoir.

![reagent plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt2/Screen+Shot+2021-07-16+at+12.45.48+PM.png)

* TWB on Slot 4:

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt2/Screen+Shot+2021-07-16+at+12.46.21+PM.png)

---

### Protocol Steps
1. Transferring 5ul of TSB from mastermix plate to sample plate, slowly mix, new tips
2. Pause
3. Sample plate is being place on magnetic module
4. Engage magnet
5. Delay 5 minutes
6. Remove supernatant (30ul)
7. Disengage magnet
8. Add 50ul of twb over beads, mix 15 times at bead location (resuspend)
9. Engage magnet
10. Repeat (5-9) 2 times, remove 50ul instead of 30 for 2nd and 3rd iteration
11. Disengage magnet
12. Add 50ul of twb over beads, mix 15 times at bead location (resuspend)
13. Pause
14. User will put EPM mastermix into columns 3 and 4 of bio rad plate
15. Engage magnet
16. Remove supernatant (50ul)
17. Disengage magnet
18. Add 20ul of EPM, mix 15 times at bead location (resuspend)
19. Pause
20. Transfer 5ul of index to sample, mix 10 times


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
0bf4f4-pt2
