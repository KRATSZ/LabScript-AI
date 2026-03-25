# Protocol Title 
Nucleic Acid Purification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Purification

## Description
This is a Nucleaic Acid Purification Protocol for the OT-2 liquid handling system

The protocol is broken down into 3 main parts:
* Pipette mixing of lysates, binding buffer and magnetic beads
* Bead washing 3x using magnetic module
* Final elution to PCR plate

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 6) to the elution PCR plate (slot 3). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [OT-2 Filter Tips, 200µL](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [NEST 2 mL 96-Well Deep Well Plate, V Bottom](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 1-Well Reservoir, 195 mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* 
* [Opentrons Tough 0.2 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/tough-0.2-ml-96-well-pcr-plate-full-skirt/)


### Pipettes
* [P300 GEN2 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ff0c3/deck.png)
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ff0c3/liquids.png)


---

### Protocol Steps
1. Mix lysate, bind, and magnetic beads with pipetting for approx. 10 min in a 2 mL block
2. Apply magnet for 10 min 
3. Remove supernatant from each sample well and discard in liquid waste reservoir. 
4. Transfer 500 uL of wash buffer from a 195 mL reservoir to each sample well in the 2 mL block
5. Mix with pipetting in each sample well
6. Apply magnet for 5 min
7. Remove 500 uL of wash buffer from each sample well and discard in the liquid waste reservoir.
8. Repeat steps 4-7 for a total of 3 washes
9. Air dry beads for 5 min
10. Transfer 50 uL of elution buffer from a 12-column reservoir to each sample well in the 2 mL block 
11. Mix beads with pipetting for 5 min
12. Apply magnet for 2 min
13. Transfer the 50 uL elution buffer containing DNA to a 96 well skirted PCR plate

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
0ff0c3
