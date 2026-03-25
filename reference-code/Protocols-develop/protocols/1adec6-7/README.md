# ProcartaPlex Protocol-2 [7/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part seven of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
This protocol is the second half of a custom, ProcartaPlex protocol - the first half can be found [here](./1adec6-6). This protocol begins after the overnight incubation from the first half with two wash steps. After the washes, 25µL of Detection Antibodies are added to the wells and the user is prompted to remove the plate for off-deck processing. Once the plate is returned, two more wash steps occur. Once the washes are complete, 50µL of SAP is added to the wells and the user is again prompted to remove the deck for off-deck processing. Once the plate is returned, the final two wash steps occur, before 120µL of Reading Buffer is added to the wells - completing the automated portion of this workflow.

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the P300-Multi Pipette is attached to.
* **Number of destination plates**: Select how many destination plates will be used in the protocol (1, 2, or 3).


---

### Labware
* [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* ProcartaPlex 96-Well Cell Culture Plates
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette)

### Reagents
* Wash Buffer
* Detection Antibodies
* SAP
* Reading Buffer

---

### Deck Setup
**Slot 1**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
</br>
**Slot 2**: **Optional**, [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (2)</br>
</br>
**Slot 3**: **Optional**, [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (3)</br>
</br>
**Slot 4**: Destination Plate (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 5**: **Optional**, Destination Plate (2) (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 6**: **Optional**, Destination Plate (3) (ProcartaPlex 96-Well Cell Culture Plate)</br>
</br>
**Slot 7**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>


### Reagent Setup
1. Load **Wash Buffer** in **Columns 1-6** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
2. Load **Detection Antibodies** in **Column 8** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
3. Load **SAP** in **Column 10** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
4. Load **Reading Buffer** in **Column 12** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
**Note**: If processing multiples plates, repeat this setup in another [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) for each additional plate


---

### Protocol Steps
1. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 1) to all the wells of the Destination Plate, and drop used tips in the waste bin.
2. User will be prompted for off-deck processing.
3. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 2) to all the wells of the Destination Plate, and drop used tips in the waste bin.
4. User will be prompted for off-deck processing.
5. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Detection Antibodies (Column 8) to all the wells of the Destination Plate, and drop used tips in the waste bin.
6. User will be prompted for off-deck processing.
7. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 3) to all the wells of the Destination Plate, and drop used tips in the waste bin.
8. User will be prompted for off-deck processing.
9. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 4) to all the wells of the Destination Plate, and drop used tips in the waste bin.
10. User will be prompted for off-deck processing.
11. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute SAP (Column 10) to all the wells of the Destination Plate, and drop used tips in the waste bin.
12. User will be prompted for off-deck processing.
13. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 5) to all the wells of the Destination Plate, and drop used tips in the waste bin.
14. User will be prompted for off-deck processing.
15. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Wash Buffer (Column 6) to all the wells of the Destination Plate, and drop used tips in the waste bin.
16. User will be prompted for off-deck processing.
17. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips, distribute Reading Buffer (Column 12) to all the wells of the Destination Plate, and drop used tips in the waste bin.
18. User will be prompted for off-deck processing (end of this protocol).



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
1adec6-7
