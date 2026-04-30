# Nucleic Acid Purification with Magnetic Beads

### Author

[Opentrons](https://opentrons.com/)



## Categories

* Nucleic Acid Extraction & Purification
    * Nucleic Acid Purification

## Description

This protocol automates the purification of nucleic acids using magnetic beads. It can support up to 96 samples in multiples of 8 using the P300 Multichannel pipette. The purification process is performed using the magnetic module for the OT-2.

Explanation of parameters below:

- `P300 Multichannel GEN2 Mount Position`: Specify which mount (left or right) to load the P300 single channel pipette.
- `Number of Samples`: Total number of samples (multiples of 8).
- `Magnet Engage Height (mm)`: The height the magnet should be raised in millimeters.
---

### Modules

* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Pipettes

- [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4a5f32/4a5f32_deck.png)

---

### Protocol Steps

Bead transfer

1. Pause until told to resume – ‘Set the deck up as per the SOP’
2. Pick up tips from A1-H1 – position 7
3. Move to channel 1 of reagent plate in position 5
4. Aspirate 20ul beads in channel 1 - 3mm from bottom, mix (150ul vol, 2 times), air gap 20ul
5. Dispense beads into A1-H1 of sample plate on the magnetic module – 2mm above top of well, blow out to destination well
6. Repeat steps 3 and 4 to dispense beads in entire plate
7. Drop tips to waste
8. Pause for 5 mins - ‘5 Min incubation to allow bead binding’
9. Engage magnet 10mm
10. Pause for 3 mins - ‘3 min incubation to allow beads to move to magnet’

Removal of supernatant

11. Pick up tips A1-H1 – position 2
12. Aspirate 40ul of supernatant from A1-H1 of sample plate on magnetic module – 2mm from bottom, slow speed
13. Dispense into the middle of waste trough in position 1 - 10mm from bottom, blow out to destination well
14. Eject tips back into same position of tip box in position 2
15. Repeat steps 11 to 14 to remove waste from the whole plate using the corresponding tips for each column

Ethanol Washes

16. Pick up tips A2-H2 – position 7
17. Move to channel 3 of reagent plate in position 5
18. Aspirate 100ul – 3mm from bottom, air gap 20ul
19. Dispense to column A1-H1 of sample plate on the magnetic module – 2mm above well top, blow out to destination well
20. Repeat steps 18-19 to add liquid to all wells
21. Drop tips to waste
22. Pause for 30 secs - ‘Incubate for 30 seconds at RT’
23. Pick up tips A1-H1 – position 2
24. Aspirate 100ul of wash buffer from A1-H1 of sample plate on magnetic module – 2mm from bottom, slow speed
25. Dispense into the middle of waste trough in position 1 - 10mm from bottom, blow out to destination well
26. Eject tips back into same position of tip box in position 2
27. Repeat steps 23 to 26 to remove waste from the whole plate using the corresponding tips for each column
28. Pick up tips A3-H3 – position 7
29. Move to channel 4 of reagent plate in position 5
30. Repeat steps 18 to 27 so that two complete ethanol washes have been carried out

Elution Stage

31. Pause for 10 mins – ‘Air dry the pellet for 10mins at RT’
32. Disengage the magnet
33. Pick up tips A4-H4 – position 7
34. Move to channel 5 of reagent plate in position 5
35. Aspirate 20ul – 3mm from bottom
36. Dispense into column A1-H1 of sample plate on the magnetic module – 3mm from bottom, mix 10ul vol, 5 times, blow out destination well
37. Drop tips to waste
38. Repeat steps 33 to 37 to add elution buffer to entire plate
39. Pause for 10 mins – ‘Incubate at RT for 10 mins to elute the sample off the beads’
40. Engage magnet
41. Pause for 2 mins- ‘Incubate at RT for 2 mins to allow beads to move to magnet’
42. Pick up tips A4-H4 – position 8
43. Aspirate 20ul from A1-H1 of sample plate on the magnetic module – 1mm from bottom
44. Dispense 20ul into A1-H1 of elution plate in position 3, blow out destination well
45. Drop tips to waste
46. Repeat steps 42-45 so that all sample eluate has been transferred to the elution plate

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

4a5f32
