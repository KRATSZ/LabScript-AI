# Nucleic Acid Purification With Omega MagBind TotalPure NGS Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
     * Nucleic Acid Purification

## Description
With this protocol, your robot can perform a bead clean-up of up to 96 input samples using Omega MagBind TotalPure NGS Beads.

## Protocol Steps

Set up: Please see pause comments displayed in the script and in the OT app.

The OT-2 will perform the following steps:
Step 1: With 8-channel 300ul pipette, mix 100ul, 2x - MagBeads in column 1 of NEST 12-well, 15ml reservoir. Quick mix before each aspiration as beads settle quickly.
Step 2: Transfer 36ul beads to NEST 100ul full-skirt plate (PCR1) on the Magnetic Module. Mix 50ul 6x with new tips for each column.
Step 3: After 2 min pause, engage magnet for bead separation.
Step 4: With 200ul filter tips, aspirate out 60 ul supernatant from each well. (Park tips here). Dispense waste liquid to column 12 of reservoir.
Step 5: With a new column of 200ul filter tips, add 80ul 80 percent EtOH (12-well reservoir) to each well. Use the same tips for whole plate. Dispense a few mm above well. Eject to trash.
Step 6: With parked tips from step 4, aspirate out 85ul supernatant from each well. Dispense waste liquid to column 11 of reservoir. Park tips.
Step 7: Repeat Steps 5 and 6. Parked tips can be ejected in waste now.
Step 8: Delay 5 min to allow EtOH evaporation from beads.
Step 9: Disengage magnet.
Step 10: Add 43 ul H20 (from reservoir), into each well of PCR1 on the Magnetic Module. Mix 10x to suspend beads.
Step 11: After 2 min incubation, engage magnet.
Step 12: Transfer 40ul eluted DNA into a new 96-well plate (PCR2) in slot 1.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p300](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Magnetic Module with NEST 100 ul PCR Plate (Deck Slot 3)
* Opentrons 200 ul filter tips (Deck Slots 5, 6, 7, 8, 10)
* NEST 12-Well Reservoir (Deck Slot 4)
* Clean 96-Well PCR Plate for eluate (Deck Slot 1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 96)" in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6d2e65
