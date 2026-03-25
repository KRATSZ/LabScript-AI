# NucleoMag Blood for DNA purification from blood

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This protocol extracts DNA using the [Nucleomag blood DNA kit](https://www.mn-net.com/us/nucleomag-blood-200-l-for-dna-purification-from-blood-744501.4). Pro-k is added to sample, as well as bead buffer. Supernatant is removed with magnets engaged before a dispense of 200ul of mbl3. After supernatant is again removed, ethanol is dispensed and removed in wash before mbl5 is added to sample. The final product is moved to the elute plate on slot 2.

Explanation of complex parameters below:
* `Number of Columns`: Specify the number of sample columns to run.
* `Use filter tips`: Specify whether this run will use filter tips or regular tips.
* `mbl5 Volume`: Specify the mbl5 volume in microliters.
* `Magnetic engage height (mm)`: Specify the engage height for the magnets to raise under the base of the magnetic plate. The engage height should be empirically tested.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) to host the P300 multi-channel pipette.



---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* [Opentrons 200ul or 300ul tips](https://shop.opentrons.com/universal-filter-tips/)
* [NEST 12 Well Reservoir](https://shop.opentrons.com/verified-labware/well-reservoirs/)
* Abgene 96 Well Plate 700ul
* Macherey Nagel 96 Squarewell Block

### Pipettes
* [P300 Multi-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* Note: reagents in reservoirs are in the order of the colors from left to right.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/33a449/Screen+Shot+2022-02-03+at+9.02.45+AM.png)



### Reagent Setup
Below find the number of columns to host select reagents depending on the number of columns run. Reagent should always be split equally between wells for the number of columns given below. For reagents only ever requiring one well, ensure that a dead volume of at least 2mL by the end of the protocol, not the beginning.
![reagent columns](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/33a449/Screen+Shot+2022-02-03+at+9.05.23+AM.png)

---

### Protocol Steps
1. Dispense 50uL Proteinase K buffer in each well of 96 well plate; need to mix each well as it is added
2. Dispense 162.5uL bead buffer in to each well; need to mix each well as it is added. It is important the bead buffer is thoroughly mixed in reservoir prior to addition to each well or the beads will settle to the bottom of the reservoir
3. Place plate on magnet for 3 minutes
4. Remove supernatant from all wells without disturbing the beads (may need 2 steps to be able to remove all supernatant)
5.Remove plate from magnet. Add 400uL MBL3 buffer to all wells; may need two steps to accomplish this. Mix each well as buffer is added.
6. Place plate back on magnet for 3 minutes
7. Remove supernatant from all wells without disturbing the beads (may need 2 steps to be able to remove all supernatant
8. Remove plate from magnet. Add 400uL MBL3 buffer to all wells; may need two steps to accomplish this. Mix each well as buffer is added.
9. Place plate back on magnet for 3 minutes
10. Remove supernatant from all wells without disturbing the beads (may need 2 steps to be able to remove all supernatant)
11. Remove plate from magent. Add 400uL 80% ethanol; mix each well as ethanol is added
12. Place plate back on magnet for 3 minutes
13. Remove supernatant from all wells without disturbing the beads (may need 2 steps to be able to remove all supernatant)
14. Allow plate to airdry on magnet for 20 minutes
15. Remove plate from magnet. Add 100 or 50uL MBL5 buffer to each well; mix each well as it is added
16. Place plate on magnet for 3 minutes
17. Transfer 50 or 100uL from each well in to a final DNA storage plate (do not disturb beads)

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
33a449
