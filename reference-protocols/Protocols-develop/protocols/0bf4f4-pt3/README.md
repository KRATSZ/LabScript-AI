# Ilumina DNA Prep Part 3 - Clean up Libraries

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina DNA Prep

## Description
This protocol is part 3 of a 3 part series which preps a 96 well Bio-Rad 200ul plate in accordance with the [Ilumina DNA Prep Kit](https://emea.support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf).

* [Part 1: Tagment DNA](https://protocols.opentrons.com/protocol/0bf4f4)
* [Part 2: Cleanup libraries](https://protocols.opentrons.com/protocol/0bf4f4-pt2)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples for this run.
* `Plate A Start Column`: Specify which column to start on plate A.
* `Plate B Start Column`: Specify which column to start on plate B.
* `Plate C Start Column`: Specify which column to start on plate C.
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

* Deck setup with a full plate of samples and pre-populated mag beads in Plate B. Note: if the protocol runs out of tips, it will pause and prompt the user to replace all tip racks. Tip boxes will be used in the order of the following slots for 200ul tips: Slot 7, 8, 9, 10. Tip rack on slot 11 will always be used for the ethanol wash step, as it will use parked tips, no matter how many samples.  

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt3/Screen+Shot+2021-07-19+at+11.39.37+AM.png)

### Reagent Setup

* Reservoir on Slot 5

![reagent plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt3/Screen+Shot+2021-07-19+at+11.39.55+AM.png)


---

### Protocol Steps
1. Engage magnetic module
2. Delay 5 minutes
3. Aspirate 22.5 supernatant, transfer to Plate A (start column parameter)
4. Disengage magnet
5. Pause (user removes plate on magnetic module, switches for Plate A, add plate B to deck))
6. Pre Mix 10 times diluted beads for whole run
7. Add 42.5ul of diluted beads to Plate A
8. Mix 10 times
9. Delay 5 minutes
10. Engage magnet
11. Delay 5 minutes
12. Transfer supernatant (62.5ul) from Plate A on magnetic module to plate B on deck already populated with magnetic beads, mix 10 times
13. Delay 5 minutes
14. Pause remove plate A on mag module for plate B
15. Engage magnet
16. Delay 5 minutes
17. Remove supernatant 65ul
18. Transfer 200ul ethanol to samples
19. Delay 30 seconds
20. Remove supernatant (200)
21. Repeat 18-20
22. P20 20ul remove from well
23. Delay 5 minutes
24. Pause
25. Add 32 ul of rsb buffer on beads (same side as beads)
26. Disengage magnet
27. Resuspend beads
28. Delay 2 minutes
29. Engage magnet
30. Delay 3 minutes
31. Transfer 30ul to place c (final elute)


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
0bf4f4-pt3
