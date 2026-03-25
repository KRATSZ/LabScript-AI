# Zymo Quick-DNA/RNA Viral Kit [Custom]

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Kit

## Description
This protocol automates nucleic acid purification with the [Zymo Quick-DNA/RNA Viral MagBead Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead) and is a modifed version of [this protocol](https://protocols.opentrons.com/protocol/zymo-quick). In this version, tips are conserved to allow for a fully automated run of 96 samples.</br>
</br>
**Update (July 24, 2021)**: Added a new parameter - *Number of Samples* - to allow user to specify the number of samples used per run.</br>
</br> 

Explanation of complex parameters below:
**Number of Samples (1-96)**: Specify how many samples are used</br>
**P300-Multi Generation**: Select which P300-Multi is being used</br>
**P300-Mult Mount**: Select which mount the pipette is attached to</br>
**Magnetic Module Generation**: Select which version of the Magnetic Module is used

---

### Modules
* [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* (5) [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) (recommended) or [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* (1) [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* (2) [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* (2) [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* (1) VWR Deepwell Plate, 1mL

### Pipettes
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* [Zymo Quick-DNA/RNA Viral MagBead Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead)

---

### Deck Setup
</br>
**Slot 1:** [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) with reagents</br>
**Slot 2:** [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 3:** [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
**Slot 4:**:[NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) with reagents</br>
**Slot 5:** [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 6:** [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 7:** [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with VWR Deepwell Plate loaded with 300µL of sample
**Slot 8:** [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 9:** [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 10:** [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml), empty for liquid waste</br>
**Slot 11:** [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml), empty for liquid waste</br>
</br>

### Reagent Setup
**Viral DNA/RNA Buffer + MagBinding Beads**: In slots 1-4 in the 12-well reservoir (deck slot 4). Each slot should have at least 14.5mL.</br>
**MagBead DNA/RNA Wash 1**: In slots 5-8 in the 12-well reservoir (deck slot 4). Each slot should have 13.5mL.</br>
**MagBead DNA/RNA Wash 2**: In slots 9-12 in the 12-well reservoir (deck slot 4). Each slot should have 13.5mL.</br>
**Ethanol Wash 1**: In slots 1-4 in the 12-well reservoir (deck slot 1). Each slot should have 13.5mL.</br>
**Ethanol Wash 2**: In slots 5-8 in the 12-well reservoir (deck slot 1). Each slot should have 13.5mL.</br>
**Nuclease-Free Water**: In slot 12 in the 12-well reservoir (deck slot 1). At least 5.5mL of NF-Water should be used.</br>


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
zymo-quick-96
