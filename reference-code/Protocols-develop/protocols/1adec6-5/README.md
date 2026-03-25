# Custom Supernatant Removal and PrestoBlue test [5/7]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Assay

## Description
**Updated**</br>
This protocol has been updated based on feedback from the user.
</br>
This protocol is part five of a larger workflow. The entire workflow can be found below</br>

Part 1: [Small Molecule Library Prep](./1adec6)</br>
Part 2: [Seed Cells](./1adec6-2)</br>
Part 3: [Transfer Small Molecules](./1adec6-3)</br>
Part 4: [Transfer Small Molecules - CSV Input](./1adec6-4)</br>
Part 5: [Custom Supernatant Removal](./1adec6-5)</br>
Part 6: [ProcartaPlex Protocol-1](./1adec6-6)</br>
Part 7: [ProcartaPlex Protocol-2](./1adec6-7)</br>
</br>
In this protocol, the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) transfers 220µL of supernatant from source plate containing cells to a destination plate. Once complete, the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will transfer 100µL of Cell medium+10% PrestoBlue to the original source plate.

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the P300-Multi Pipette is attached to.
* **Aspirate from Well Bottom Height**: Specify the height from the bottom of the well (in mm) that the pipette will aspirate supernatant (note: default height is 1mm from bottom).
* **Perform 2nd aliquot**: Specify whether or not to perform a second aliquot (110µL transferred to plate in slot 5)


---

### Labware
* [Opentrons 300µL Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* SPL 96-Well Cell Culture Plates
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)

### Pipettes
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette)

### Reagents
* Cell medium+10% PrestoBlue

---

### Deck Setup
**Slot 1**: Source Plate, containing Cells (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 4**: Destination Plate (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 5**: **Optional**, Second Destination Plate (SPL 96-Well Cell Culture Plate)</br>
</br>
**Slot 6**: [[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
</br>
**Slot 7**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)</br>
</br>


### Reagent Setup
1. Load Cell medium+10% PrestoBlue in **Column 2** of the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)


---

### Protocol Steps
1. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips.
2. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will transfer 220µL of supernatant from Column 1 of the Source Plate to Column 1 of the Destination Plate.
3. If performing the second aliquot, the [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will transfer 100µL of supernatant from Column 1 of the Source Plate to Column 1 of the Second Destination Plate.
4. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will drop used tips in the waste bin.
5. Steps 1-4 will be repeated for columns 2-10.
6. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will pick up tips.
7. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will mix Cell medium+10% PrestoBlue, then transfer 100µL of Cell medium+10% PrestoBlue to Column 1 of the Source Plate (dispensing at the top of the well).
8. Step 7 will be repeated for columns 2-10 of the Source Plate.
9. [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-Channel-electronic-pipette) will drop used tips in the waste bin.
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
1adec6-5
