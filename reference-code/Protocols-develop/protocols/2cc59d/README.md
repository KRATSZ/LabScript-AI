# ELISA Assay Semi-Automated

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol performs an ELISA assay between two 96 well plates. For detailed instruction, please see protocol steps below. Stop solution and TMB should only be added when prompted by the protocol upon a pause step. The protocol will automatically pause if it runs out of tips, prompting the user to replace. Tip boxes should always be placed in order of slot 7, 8, and 9 on the deck, even if running low sample numbers. Tip box on slot 9 is always used for 4 wash steps.

Explanation of complex parameters below:
* `Number of samples (1 to 38)`: Specify the number of samples for this run. The protocol will run as many columns rounding up on the number of samples provided.
* `P20/P300 Pipette Mounts`: Specify which mount (left or right) to host the P20 and P300 pipettes.

---

### Labware
* [NEST 12 Well Reservoir](https://shop.opentrons.com/)
* [NEST 1 Well Reservoir](https://shop.opentrons.com/)
* [Opentrons 300ul Tips](https://shop.opentrons.com/)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/)
* [Opentrons 4-in-1 tube rack with 1.5mL safe-lock Eppendorf tubes](https://shop.opentrons.com/)
* Greiner 96 Plate
* Costar 96 Plate


### Pipettes
* [P20 Single Channel Pipette](https://opentrons.com/pipettes/)
* [P300 Multi Channel Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup
![OT-2 deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2cc59d/Screen+Shot+2022-06-09+at+2.24.39+PM.png)

### Reagent Setup
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2cc59d/Screen+Shot+2022-04-29+at+2.46.57+PM.png)
![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2cc59d/Screen+Shot+2022-04-29+at+2.47.12+PM.png)

---

### Protocol Steps
1. Transfer 270 µL of sample dilution buffer from column 1 of the 12 well reservoir to A1 on the Greiner 96 well plate with the p300 multichannel pipette
2. Transfer 150 µL of sample dilution buffer from column 1 of the 12 well reservoir to wells B1-H1 on the Greiner 96 well plate with the p300 multichannel pipette (same tips)
3. Transfer 126 µL of sample dilution buffer from column 1 of the 12 well reservoir to all wells in columns 3, 5, 7, 9, and 11 of the Greiner 96 well plate with the p300 multichannel pipette
4. Transfer 30 µL of pre-diluted Calibrator Stock from position A1 on tube rack to A1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution for steps 3-9)
5. Transfer 150 µL of the contents from A1 to B1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
6. Transfer 150 µL of the contents of B1 to C1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
7. Transfer 150 µL of the contents from C1 to D1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
8. Transfer 150 µL of the contents from D1 to E1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
9. Transfer 150 µL of the contents from E1 to F1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
10. Transfer 150 µL of the contents from F1 to G1 on the Greiner 96 well plate, mix 5 times (can change number of times mixed based on what’s most appropriate for a serial dilution)
11. Transfer 14 µL of positive control from A2 on tube rack 1 to well G3 on the Greiner 96 well plate with the p20 single channel pipette, mix 3-5 times
12. Transfer 14 µL of negative control from A3 on tube rack 1 to well H3 on the Greiner 96 well plate with the p20 single channel pipette, mix 3-5 times
13. Transfer 120 µL RBD-HRP solution from column 2 on the 12 well reagent reservoir to all wells in column 2
14. Transfer 120 µL RBD-HRP solution from column 2 on the 12 well reagent reservoir to all wells in columns 4, 6, 8, 10, and 12 of the Greiner 96 well plate (can be same tips as the above step and for all columns in this step)
15. (NOTE: Steps 15-20 should take less than 2 minutes) Using the p300 multichannel pipette, transfer 120 µL of each well of column 1 on the Greiner plate into the corresponding well on column 2 of the same plate (i.e., A1 goes to A2, B1 to B2, etc.), mix 2 times
16. Using the p300 multichannel pipette, transfer 120 µL of each well of column 3 on the Greiner plate into the corresponding well in column 4 of the same plate (i.e., A3 goes into A4, B3 to B4, etc.), mix 2 times
17. Using the p300 multichannel pipette, transfer 120 µL of each well of column 5 on the Greiner plate into the corresponding well in column 6 of the same plate (i.e., A5 goes into A6, B5 to B6, etc.), mix 2 times
18. Using the p300 multichannel pipette, transfer 120 µL of each well of column 7 on the Greiner plate into the corresponding well in column 8 of the same plate (i.e., A7 goes into A8, B7 to B8, etc.), mix 2 times
19. Using the p300 multichannel pipette, transfer 120 µL of each well of column 9 on the Greiner plate into the corresponding well in column 10 of the same plate (i.e., A9 goes into A10, B9 to B10, etc.), mix 2 times
20. Using the p300 multichannel pipette, transfer 120 µL of each well of column 11 on the Greiner plate into the corresponding well in column 12 of the same plate (i.e., A11 goes into A12, B11 to B12, etc.), mix 2 times
21. Immediately after step 20, move the Greiner 96 well plate to the temperature module (slot 9) at 37°C for 30 minutes
22. (Note: Steps 22-27 should be completed in less than 2 minutes) (Note: Increase amount aspirated if needed) Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 2 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 1 and 2 on the costar plate (i.e., A2 on the Greiner plate is transferred in duplicate into A1 and A2 on the Costar plate)
23. Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 4 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 3 and 4 on the costar plate (i.e., A4 on the Greiner plate is transferred in duplicate into A3 and A4 on the Costar plate, A3 and A4 on Costar will contain 100 µL)
24. Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 6 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 5 and 6 on the costar plate (i.e., A6 on the Greiner plate is transferred in duplicate into A5 and A6 on the Costar plate)
25. Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 8 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 7 and 8 on the costar plate (i.e., A8 on the Greiner plate is transferred in duplicate into A7 and A8 on the Costar plate)
26. Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 10 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 9 and 10 on the costar plate (i.e., A2 on the Greiner plate is transferred in duplicate into A9 and A10 on the Costar plate)
27. Using the p300 multichannel pipette, aspirate 200 µL of all wells in column 12 on the Greiner plate and transfer 100 µL into the corresponding wells in columns 11 and 12 on the costar plate (i.e., A12 on the Greiner plate is transferred in duplicate into A11 and A12 on the Costar plate)
28. Immediately after the last step, the Costar 96 well strip plate should be incubated at 37 °C for 15 minutes on the temperature block in slot 9
29. Using the p300 multichannel pipette, aspirate 100 µL from all wells in column 1
30. Repeat step 29 for all columns on the Costar plate
31. (NOTE: steps 31-??? Should be completed in less than 2 minutes) (NOTE: This section can be altered to make the wash steps faster/more efficient) Transfer 260 µL of wash buffer into all wells in column 1
32. Repeat step 31 for all columns on the Costar plate (same tips as step 31)
33. Aspirate 260 µL from all wells in column 1 (keep tips for following washes)
34. Repeat step 33 for all columns on the plate (keep tips for each column to reuse for rest of wash steps- 4 washes total)
35. Repeat steps 31-34 for a total of 4 washes per well
36. Add approximately 10 mL of TMB solution into column 3 of the 12 well reagent reservoir (this reagent is light sensitive)
37. Using the p 300 multichannel pipette, transfer 100 µL of TMB from column 3 of the 12 well reagent reservoir to all wells on the Costar plate column by column (start with column 1, then column 2 and so on)
38. Remove the Costar 96 well plate from the OT-2 and incubate for 15 minutes in the dark (typically in a drawer) at room temperature (done by the person performing the test)
39. Place the Costar 96 well plate back into its slot on the OT-2 (done by the person performing the test)
40. Fill column 4 on the 12 well reagent reservoir with approximately 5 mL of stop solution (this reagent is light sensitive) (done by the person performing the test)
41. Transfer 50 µL of stop solution to all wells in column 1
42. Transfer 50 µL of stop solution to all wells in column 2
43. Transfer 50 µL of stop solution to all wells in column 3
44. Transfer 50 µL of stop solution to all wells in column 4
45. Transfer 50 µL of stop solution to all wells in column 5
46. Transfer 50 µL of stop solution to all wells in column 6
47. Transfer 50 µL of stop solution to all wells in column 7
48. Transfer 50 µL of stop solution to all wells in column 8
49. Transfer 50 µL of stop solution to all wells in column 9
50. Transfer 50 µL of stop solution to all wells in column 10
51. Transfer 50 µL of stop solution to all wells in column 11
52. Transfer 50 µL of stop solution to all wells in column 12
53. End of protocol- remove Costar plate from OT-2 and immediately read on the MultiSkan FC photometer at 450 nm

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
2cc59d
