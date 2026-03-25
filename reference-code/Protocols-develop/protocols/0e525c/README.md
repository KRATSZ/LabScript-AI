# droplet digital PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs a custom ddPCR prep in semi-skirted PCR plates using an adapter to fit into the deck slots.

---
### Labware
* [OT-2 Filter Tips, 200µL (999-00081)](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [OT-2 Filter Tips, 20µL (999-00099)](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [P300 GEN2 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 GEN2 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [DPBS](link to product not available)
* [Nuclease-Free Water](link to product not available)
* [Master Mix](link to product not available)

---

### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e525c/deck.png)
![liquids](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e525c/liquids+map.png)
![legend](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0e525c/liquids+legend.png)

### Reagent Setup
* Custom labware (Biorad 96-well semi-skirted PCR plate with deck adapter) - Deck Slot 5
Columns 1-8 dPBS
Column 9 Test Article
Column 11 Master Mix
Column 12 Nuclease-free Water


---

### Protocol Steps
1. Transfer 180 uL of DPBS into columns 1-7 of dest plate 1
2. Transfer 160 uL DPBS into column 8 of dest plate 1
3. Transfer 20 uL of Test Article into column 1 of dest plate 1, mix 20 times
4. Preform serial dilutions from column 1 thru column 7: transfer 20 uL between columns, mix 20 times (new tips between each column)
5. Transfer 40 uL from column 6 of dest plate 1 to column 8 of dest plate 1, mix 20 times
6. Transfer 20 uL master mix to dest plate 2 columns 1-5
7. Transfer 5 uL from column 6 on dest plate 1 to column 1 on dest plate 2
8. Transfer 5 uL from column 7 on dest plate 1 to column 2 on dest plate 2
9. Transfer 5 uL from column 8 on dest plate 1 to column 3 on dest plate 2
10. Transfer 5 uL (water) to columns 4-5 on dest plate 2 (new tips between each transfer)

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
0e525c