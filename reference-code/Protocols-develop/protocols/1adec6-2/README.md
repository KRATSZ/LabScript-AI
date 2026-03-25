# Seed Cells [2/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part two of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
In this protocol, 250µL of cells are transferred from the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) to the SPL 96-Well Cell Culture Plates.

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the P300-Multi Pipette is attached to.
* **Number of Destination Plates**: Select the number of destination plates.

---

### Labware
* [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* SPL 96-Well Cell Culture Plates (Round Bottom)

### Pipettes
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* Cells (Column 3 of 12-Well Reservoir)
* Cells (Column 4 of 12-Well Reservoir)

---

### Deck Setup
**Slot 1**: Destination Plate 1 (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 2**: Destination Plate 2 (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 3**: Destination Plate 3 (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 4**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
</br>
**Slot 7**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>



### Reagent Setup
1. Load Cells in **Column 3** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
2. Load Cells in **Column 4** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
3. Load Cells in **Column 5** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for Plate 2)
4. Load Cells in **Column 6** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for Plate 2)
5. Load Cells in **Column 7** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for Plate 3)
6. Load Cells in **Column 8** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for Plate 3)

---

### Protocol Steps
1. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up tips.
2. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will mix Cells in **Column 3** of [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml).
3. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer 250µL of Cells from [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) to Columns 1-6 of the first Destination Plate (Slot 1).
4. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will drop used tips in the waste bin.
5. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up tips.
6. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will mix Cells in **Column 4** of [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml).
7. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer 250µL of Cells from [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) to Columns 7-12 of the first Destination Plate (Slot 1).
8. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will drop used tips in the waste bin.
9. Steps 1-8 will repeat for each additional destination plate, accessing the following two channels of the reservoir for each plate.
10. End of the protocol.

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
1adec6-2
