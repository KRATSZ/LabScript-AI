# Transfer Small Molecules - CSV Input [4/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part four of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
In this protocol, a CSV is used to dictate the volume and destination of liquid transfers using the [P20 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette).

Explanation of complex parameters below:
* **P20 Mount**: Select which mount the P20 Pipette is attached to.
* **P20 Selection (Single or Multi)**: Select which pipette is used (please see note below)
* **Transfer CSV**: Upload the CSV containing the liquid transfers. The CSV should be formatted as follows:</br>
</br>

| Source Well | Volume | Destination Well |</br>
| ----------- | ------ | ---------------- |</br>
| A1          | 3      | C2               |</br>
| A1          | 2      | B4               |</br>
| A2          | 5      | D7               |</br>

**Note**: If using the [P20 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette), you should only use Row A when selecting a *destination well* in the CSV.

---

### Labware
* [Opentrons 20µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)
* [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Thermo-Fast 96-Well, Fully Skirted Plate
* SPL 96-Well Cell Culture Plates

### Pipettes
* [P20 Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette)
* [P300 8-Channeel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette)

### Reagents
* Small Molecule Library

---

### Deck Setup
**Slot 1**: Small Molecule Library Plate (Thermo-Fast 96-Well, Fully Skirted Plate)</br>
</br>
**Slot 2**: Destination Plate (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 3**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 4**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 5**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 7**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 8**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 10**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>
**Slot 11**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-tips)</br>
</br>


---

### Protocol Steps
For each of the lines in the CSV, the following steps will occur:
1. [P20 Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette) will pick up a tip.
2. [P20 Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette) will mix library in corresponding column.
3. [P20 Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette) will transfer specified volume from the well of the source plate to the well of the destination plate listed in the CSV.
4. [P20 Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/Single-Channel-electronic-pipette) will drop used tips in the waste bin.
5. Steps 1-4 will repeat for each line in the CSV.
6. *Update*: The [P300 8-Channeel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips and mix each column that had samples transferred to it. The first set of tips will be disposed in the trash and subsequent tips will be dropped into empty slots (to save space in the waste bin).
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
1adec6-4
