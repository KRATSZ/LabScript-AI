# RNA Purification with Magnetic Beads

### Author

[Opentrons](https://opentrons.com/)



## Categories

* Nucleic Acid Extraction & Purification
    * RNA Purification

## Description

This protocol automates the purification of RNA using magnetic beads. It can support up to 94 samples and can have a custom starting well position. The protocol is also optimized for tip conservation and reuses tips for various steps.

Explanation of parameters below:

- `Number of Samples`: The total number of samples per run. The maximum samples supported is 94 samples. This value is also used to determine additional wells needed when setting a `Starting Well` below. For example, if there are 3 samples and the starting well is C7, then the sample wells for all plates will be C7, D7, E7.
- `Starting Well Name`: The well name samples should begin with for each 96 well plate in the protocol.
- `P300 Single GEN2 Mount Position`: Specify which mount (left or right) to load the P300 single channel pipette.
- `Thermocycler Hold Temperature (°C)`: The temperature the thermocycler will be set to and held for the entire protocol.
- `Magnetic Module Engage Height (mm)`: The height the magnets should raise.
- `Supernatant Removal Radius (X-dimension) (mm)`: The radius in the X-dimension of how far the pipette should move before aspirating supernatant. **Note: Only enter positive values. The protocol will automatically determine the side (+/-) based on the well/column.**
- `Supernatant Removal Aspirate Flow Rate (uL/s)`: The aspiration flow rate at which the pipette will aspirate supernatant.
- `Supernatant Removal Dispense Flow Rate (uL/s)`: The aspiration flow rate at which the pipette will dispense supernatant.

---

### Modules

* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Pipettes

- [P300 GEN2 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2905a4/2905a4_layout.png)

### Reagent Setup

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2905a4/2905a4_reagents.png)

---

### Protocol Steps

1. Set Thermocycler to 4°C
2. Dilute Magnetic Beads
3. Transfer 30uL of Magnetic Beads to Purification Plate
4. Engage Magnet to Recover beads
5. Delay for 2 minutes for attracting beads
6. Remove supernatant from the side of the well
7. Open Thermocycler Lid and Dilute Samples/Mix Samples using RNAse-free water (RFW)
8. Disengage Magnetic Module
9. Transfer Mixed Samples to Magnetic Beads and Mix
10. Add RNA Binding Buffer (RBB) to samples
11. Mix Beads with RBB and samples
12. Pause: Shake Beads on External Shaker
13. Engage Magnet to Recover beads
14. Delay for 2 minutes for attracting beads
15. Remove supernatant from the side of the well
16. Disengage Magnetic Module
17. Add Wash Buffer (WB) to Samples
18. Mix Beads with WB and samples
19. Engage Magnetic Module
20. Delay for 2 minutes for extracting beads
21. Remove WB
22. Delay for 20 minutes to allow beads to dry
23. Disengage Magnetic Module
24. Perform First Elution with RNAse-free water
25. Delay for 5 minutes to Elute RNA from the Magnet
26. Engage Magnetic Module
27. Delay for 2 minutes
28. Set Temperature Module to 4°C
29. Transfer first elution into the cooled recipient plate on the temperature module
30. Disengage Magnetic Module
31. Add fresh RNAse-free water for second eluate
32. Mix Beads with Second Elution Buffer
33. Pause for 5 minutes for eluting RNA from beads
34. Engage Magnetic Module
35. Delay for 2 minutes for extracting beads
36. Transfer second elution into the cooled recipient plate on the temperature module
37. Deactivate all modules
38. Protocol Completed!

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

2905a4
