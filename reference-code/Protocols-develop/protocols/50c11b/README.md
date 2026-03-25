# Custom PCR Setup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates two different PCR setup protocols, transferring up to 96 samples from up to 4 different source plates to a single 384-well plate.

Using the [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), samples are transferred from KingFisher 96-Deepwell plates to an Applied Biosystems MicroAmp Optical 384-Well Reaction Plate (pre-filled with mastermix), mixing the samples slightly before transfer and again after transfer.

To optimize waste bin storage and reduce the need for human interference, tips used after the first plate of transfers are replaced in the empty tiprack slots from the earlier transfers (ex. tips used for Plate 2 transfers are replaced in the tiprack used for Plate 1 transfers).

Explanation of complex parameters below:
* **Protocol Type**: If set to *Covid*, 5.3µl of sample will be transferred to the destination plate and 12µL will be mixed within the well. If set to *UTI & More*, 2µl of sample will be transferred to the destination plate and 4µL will be mixed within the well.
* **Plate 1 Number of Samples**: Specify the number of samples in Plate 1 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 2 Number of Samples**: Specify the number of samples in Plate 2 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 3 Number of Samples**: Specify the number of samples in Plate 3 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 4 Number of Samples**: Specify the number of samples in Plate 4 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **P20-Multi Mount**: Select which mount the P20-Multi Pipette is attached to.

---

### Labware
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* KingFisher 96 Deepwell Plate (containing samples)
* Applied Biosystems MicroAmp Optical 384-Well Reaction Plate

### Pipettes
* [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* Mastermix (pre-filled in 384-well plate)

---

### Deck Setup
The deck should be setup as follows:</br>
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/50c11b/50c11b_deck.png)
</br>
**Tipracks**: These will be accessed in the numbered order (starting with slot 8 and ending with slot 7)</br>
**Sample Plates**: These can be loaded as needed and with as many samples as available, with the locations of plates being static. In the image above, Plates 1 and 2 are loaded completely while Plates 3 and 4 only have 16 samples.</br>
**Destination Plate**: This is the 384-well plate and should be pre-filled with the corresponding mastermix needed for the protocol.

### Reagent Setup
The mastermix needed for the protocol should be filled into the 384-well plate beforehand. The image below illustrates how the 0T-2 transfers samples from a 96-well plate to a 384-well plate.</br>
Samples from Plate 1 and 2 will fill every other column beginning with column A; samples from Plate 1 will begin in column 1, samples from Plate 2 will begin in column 13. Samples from Plate 3 and 4 will fill every other column beginning with column B; samples from Plate 3 will begin in column 1, samples from Plate 4 will begin in column 13.
![384-well plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/50c11b/50c11b_384wellplate.png)

---

### Protocol Steps
1. For each column of samples in Plate 1, the pipette will pick up tips.
2. Samples will be mixed, then transferred to the 384-well plate (Rows A/C/E..., Columns 1-12) and mixed.
3. Tips will be disposed of in the waste bin.
4. For each column of samples in Plate 2, the pipette will pick up tips.
5. Samples will be mixed, then transferred to the 384-well plate (Rows A/C/E..., Columns 13-24) and mixed.
6. Tips will be disposed of in empty tip slots used for Plate 1.
7. For each column of samples in Plate 3, the pipette will pick up tips.
8. Samples will be mixed, then transferred to the 384-well plate (Rows B/D/F..., Columns 1-12) and mixed.
9. Tips will be disposed of in empty tip slots used for Plate 2.
10. For each column of samples in Plate 4, the pipette will pick up tips.
11. Samples will be mixed, then transferred to the 384-well plate (Rows B/D/F..., Columns 13-24) and mixed.
12. Tips will be disposed of in empty tip slots used for Plate 3.
13. End of the protocol.

### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
50c11b
