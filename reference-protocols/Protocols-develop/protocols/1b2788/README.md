# Zymo Quick-DNA Fecal/Soil Microbe 96 Magbead Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This protocol performs the Zymo Quick-DNA Fecal/Soil Microbe 96 Magbead Kit. Please find a description of the kit below from [Zymo's website](https://www.zymoresearch.com/collections/quick-dna-fecal-soil-microbe-kits/products/quick-dna-fecal-soil-microbe-96-magbead-kit):

The Quick-DNA Fecal/Soil Microbe 96 Magbead Kits are designed for the simple and rapid isolation of inhibitor-free, PCR-quality host cell and microbial DNA from a variety of sample sources, including humans, birds, rats, mice, cattle, etc. The procedure is easy and can be completed in as little as 90 minutes: fecal samples are rapidly and efficiently lysed by bead beating with our state of the art, ultra-high density BashingBeads. Zymo MagBinding Bead technology, which features Zymo Research's Inhibitor Removal technology, is then used to isolate the DNA. Eluted DNA is ideal for downstream molecular-based applications including PCR, arrays, genotyping, methylation detection, etc.

Explanation of complex parameters below:
* `Number of Columns`: Specify the number of sample columns in this run (1-12).
* `Pre-Wash buffer volume (ul)`: Specify wash volumes for both the pre-wash buffer, and gDNA wash buffer in microliters. Volumes can be greater than 200ul, and will be split if need be over multiple transfers.
* `Magnetic Module Engage Height`: Specify the magnetic module engage height in mm.
* `Elute Buffer Volume`: Specify the elute buffer volume in microliters.
* `P300 Multi-Channel Pipette Mount`: Specify which mount (left or right) to host the P300 multi-channel pipette.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* [Opentrons 200ul Filter tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*tbwww1*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0ODQ5NzQ5OC44MTIuMS4xNjQ4NDk3NzMyLjA.&_ga=2.178485476.1131955611.1648475204-1365106149.1621361358)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [NEST 1-Well Reservoirs, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* Zymo 96 well plate 1.2mL

### Pipettes
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Reagents
* [Zymo Quick-DNA Fecal/Soil Microbe 96 Magbead Kit](https://www.zymoresearch.com/collections/quick-dna-fecal-soil-microbe-kits/products/quick-dna-fecal-soil-microbe-96-magbead-kit)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1b2788/Screen+Shot+2022-04-21+at+5.12.11+PM.png)

### Reagent Setup

NOTE: For the binding buffer (A1-A4) and gDNA wash (A8-A11), if running 3 columns of samples or less, you only need fill the first trough. If running 4 columns, then the total volume should be split between troughs 1 and 2 respectively. In other words, subsequent troughs of the same reagent should always have identical volumes at the start of the run, and a new trough is added for every 3rd column of samples. If running 7 columns of samples, then equal volumes are to be delivered to the first three troughs for binding buffer and gDNA wash. If running 12 columns, equal volumes should be placed in all 4 troughs for binding buffer and gDNA wash.

If running 6 columns or less of the prewash, only A6 needs to be filled. If running more than 6 columns, the total volume should be split between A6 and A7.

* Reservoir: Slot 1
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1b2788/Screen+Shot+2022-04-21+at+5.10.43+PM.png)


---

### Protocol Steps
1. Pick-up tips from slot 4 and aspirate 200ul MagBinding Buffer from troughs 1/2/3 of NEST 12 reservoir plate in slot 1 (airgap after aspiration).
2. Dispense 200 ul MagBinding Buffer into 96 well plate with pipette tip above height of wells. Do not touch plate or samples. Blowout after dispensing.
3. Using the same tips, repeat steps 1 and 2 twice more to add 600 ul MagBinding Buffer to each well in total. Repeat across entire plate using same tips.
4. Using the same tips, premix the MagBinding Beads in trough 4 of NEST 12 reservoir plate in slot 1. Mix 50 ul for 10 cycles.
5. Aspirate 25 ul MagBinding Beads (airgap).
6. Dispense 25 ul MagBinding Beads into all wells of the 96 well plate with pipette tip above height of wells. Do not touch plate or samples. Re-use tips and use blowout to avoid drips.
7. Discard tips after final transfer.
8. Pause protocol.
9. Prompt user: “Seal plate and place on rotator. Rotate at low speed for 10 minutes”
10. Prompt user: “Now spin-down plate, unseal, and place back on mag deck.”
11. Allow user to restart protocol when ready.
12. Engage magnet. Stand 2 minutes.
13. Pick-up new tips from slot 7.
14. Using slow aspiration mode (=< 50 ul/s flow rate) aspirate 166 ul supernatant and dispense into reagent trash (slot 11). Use touch tips and blowout to avoid drips.
15. Using the same tips, repeat step 14 four more times for each column of the plate to remove 830 ul supernatant in total. Discard and change tips, taking from rack in slot 7, before moving to each new column.
15. Disengage magnet.
16. Pick-up new tips from slot 5.
17. Aspirate X ul Pre-Wash buffer from troughs 5-11 of NEST 12 reservoir plate in slot 1. Airgap.
18. Dispense X ul Pre-Wash buffer into the 96 well plate with pipette tip above height of wells. Do not touch plate or samples. Blowout after dispensing.
19. Using the same tips, repeat steps 17 and 18 to add a total volume of 300 ul Pre-Wash buffer to all wells of the 96 well plate. Do not change tips between columns on the plate.
20. Engage magnet. Stand 2 minutes.
21. Using the same tips and slow aspiration mode (=< 50 ul/s flow rate) aspirate 150 ul supernatant and dispense into reagent trash (slot 11). Use touch tips and blowout to avoid drips.
22. Re-using tips, repeat step 21 to remove 300 ul supernatant in total. After finishing each column, park tips in slot 8 to start a new column with a new set of tips from slot 5.
23. Disengage magnet.
24. Pick-up new tips from slot 4.
25. Aspirate X ul gDNA Wash buffer from NEST 1 well reservoir (troughs 7-10) in slot 1. Airgap.
26. Dispense X ul gDNA Wash buffer into the 96 well plate with pipette tip above height of wells. Do not touch plate or samples. Blowout after dispensing.
27. Using the same tips, repeat steps 25 and 26 once more to add a total volume of 300 ul gDNA Wash buffer to all wells of the 96 well plate.
28. Engage magnet. Stand 2 minutes.
29. Using parked tips from slot 8 and slow aspiration mode (=< 50 ul/s flow rate) aspirate 150 ul supernatant and dispense into reagent trash (slot 11). Use touch tips and blowout to avoid drips.
30. Using the same tips, repeat step 29 once more to remove 300 ul supernatant in total. After finishing each column, change tips, using the parked tips from slot 8.
31. Repeat steps 24 – 30 to do a second 300 ul wash with the gDNA wash buffer. Use the same parked tips for each column when removing the supernatant, but trash tips after finishing each column.
32. Pause protocol while keeping magnet engaged. Prompt user: “Drying for 30 minutes.”
33. Allow user to restart protocol when ready.
34. Disengage magnet.
35. Pick-up new tips from slot 2 (elution buffer tip rack).
36. Aspirate 50 ul DNA Elution Buffer from trough 1 of NEST 12 reservoir plate in slot 6. Airgap.
37. Dispense 50 ul DNA Elution Buffer into the 96 well plate with pipette tip 2mm above bottom of well.
38. Mix 40ul volume 25 times. Blowout and touch tips, before trashing to avoid drips.
39. Engage magnet. Stand 2 minutes.
40. Pick-up new tips from slot 9 (final elution tip rack). Aspirate 50ul Elution Buffer from the 96 well plate. Airgap.
41. Dispense 50ul Elution Buffer into the NEST 96 well 100 ul elution plate in slot 3. Trash tips.

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
1b2788
