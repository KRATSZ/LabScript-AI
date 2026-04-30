# Transfer Small Molecules [3/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part three of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
In this protocol, 1µL is transferred from the small molecule library plate to the experiment plate seeded with cells.

Explanation of complex parameters below:
* **P20-Multi Mount**: Select which mount the P20-Multi Pipette is attached to.
* **Number of Destination Plates**: Select the number of destination plates.
* **Transfer volume (in µL)**: Specify the volume to be transferred.
* **Mix with P300-Multi**: Select whether or not to add an optional mix step with the P300-Multi Pipette (200µL, 3 times) after the transfer occurs

---

### Labware
* [Opentrons 20µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)
* * [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (optional)
* Thermo-Fast 96-Well, Fully Skirted Plate
* SPL 96-Well Cell Culture Plates

### Pipettes
* [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) (optional)

### Reagents
* Small Molecule Library

---

### Deck Setup
**Slot 1**: Destination Plate 1 (SPL 96-Well Cell Culture Plat)</br>
</br>
**Slot 2**: Destination Plate 2 (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 3**: Destination Plate 3 (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 4**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 5**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (optional, for mixing)</br>
</br>
**Slot 6**: Small Molecule Library Plate (Thermo-Fast 96-Well, Fully Skirted Plate)</br>
</br>
**Slot 7**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 8**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (optional, for mixing)</br>
</br>
**Slot 10**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 11**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (optional, for mixing)</br>
</br>


---

### Protocol Steps
For each of the columns (1-10) in each destination plate (1-3), the following steps will occur:
1. [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up tips.
2. [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will mix library in corresponding column.
3. [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer 1µL from the corresponding column of the Small Molecule Library Plate to the same column of the destination plate.
4. [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will drop used tips in the waste bin.
5. **Optional**: [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up tips, mix column, drop tip (repeat for each column), if **Mix with P300-Multi** is set to **Yes**.
6. Steps 1-5 will repeat for each column/destination plate.
7. End of the protocol.

### Process
1. Input your protocol parameters above.
2. Download your protocol bundle.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1adec6-3
