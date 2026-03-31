# ProcartaPlex Protocol-1 [6/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part six of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
This protocol is the first half of a custom, ProcartaPlex protocol. In this protocol, 50µL of Magnetic Beads are added to all the wells of the Destination Plate. The user is then prompted to remove the plate and incubate off the deck before returning to the robot. Once the Destination Plate is replaced, Wash Buffer is added and then 50µL of samples (columns 1-10 of Sample Plate) and standards (columns 1 and 2 of Standards Plate) are added to the Destination Plate. The user is then prompted to perform some off-deck steps before incubating overnight. Once incubation is complete, users can move on to [ProcartaPlex Protocol-2](./1adec6-7).

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the P300-Multi Pipette is attached to.
* **Number of destination plates**: Select how many destination plates will be used in the protocol (1 or 2).


---

### Labware
* [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* ProcartaPlex 96-Well Cell Culture Plates
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette)

### Reagents
* Magnetic Beads
* Wash Buffer

---

### Deck Setup
**Slot 1**: **Optional**, Destination Plate 2 (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 2**: **Optional**, Sample Plate 2 (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 3**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
</br>
**Slot 4**: Destination Plate 1 (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 5**: Sample Plate 1 (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 6**: Standards Plate (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 7**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>
**Slot 8**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>
**Slot 10**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>

### Reagent Setup
1. Load **Magnetic Beads** in **Column 1** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
2. Load **Wash Buffer** in **Column 2** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
3. If using two destination plates, Load **Wash Buffer** in **Column 3** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)


---

### Protocol Steps
1. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips.
2. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will transfer 50µL of Magnetic Beads from Column 1 of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) to all wells of the Destination Plate (dispensing from the top of the well).
3. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will drop used tips in the waste bin.
4. User will be prompted to remove Destination Plate for off-deck processing
5. Once returned, for each transfer between the samples (Columns 1-10, Sample Plate) and standards (Columns 1, Standards Plate, two times) to Columns 1-12 of the Destination Plate, the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, mix in the source well, transfer 50µL, then dispose of used tips in the waste bin. **Optional**: If using two destination plates, samples will be transferred from the second sample plate (Columns 1-10, deck slot 2) and two times from Column 2 of the Standards Plate.
6. User will be prompted to remove Destination Plate for off-deck processing and overnight incubation (end of this protocol).

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
1adec6-6
