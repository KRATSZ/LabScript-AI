# Omega Mag-Bind Bacterial DNA 96 Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Omega Mag-Bind Bacterial DNA 96 Kit

## Description
This is a custom protocol that automates certain steps of the Omega Mag-Bind Bacterial DNA 96 Kit on the OT-2 robot. This kit allows rapid isolation of genomic DNA from bacterial samples.

Explanation of complex parameters below:
* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `P300 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `P1000 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `Magnetic Module Engage Height`: The height the magnets will raise on the magnetic module.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [PlateOne® Deep 96-Well 2 mL Polypropylene Plate](https://www.usascientific.com/plateone-96-deep-well-2ml/p/PlateOne-96-Deep-Well-2mL)

### Pipettes
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P1000 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

### Reagents
* [Omega Mag-Bind Bacterial DNA 96 Kit](https://www.omegabiotek.com/product/mag-bind-bacterial-dna-96-kit/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2a370c/2a370c.png)

### Reagent Setup

**All reagents shown in the diagram and described below are for up to 96 samples.**

* Slot 2: A1-A3 (Orange) contains MSL buffer. A7-A12 (Purple) contains SPM Buffer.
* Slot 6: A1 (Green) containse RNase A. B1 (Blue) contains Mag-Bind beads.

---

### Protocol Steps
1. Transfer 5 uL of RNase A and then mix thoroughly 20 times.
2. Incubate at room temperature for 5 minutes.
3. Transfer 400 uL of MSL Buffer to all samples.
4. Transfer 10 uL of Mag-Bind particles to all samples and mix thoroughly 20 times.
5. Transfer 528 uL of Ethanol and mix thoroughly 20 times.
6. Incubate at room temperature for 5 minutes.
7. Engage magnetic module for 15 minutes.
8. Aspirate and discard supernatant.
9. Disengage magnetic module.
10. Transfer 400 uL of SPM buffer to samples.
11. Resuspend magnetic beads and then incubate for 3 minutes at room temperature.
12. Engage magnetic module for 15 minutes.
13. Aspirate and discard supernatant.
14. Repeat steps 10-13 again.
15. Air dry magnetic beads for 5 minutes.
16. Remove residual supernatant.
17. Air dry beads for 15 minutes until they dry.
18. Disengage magnetic module.

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
2a370c