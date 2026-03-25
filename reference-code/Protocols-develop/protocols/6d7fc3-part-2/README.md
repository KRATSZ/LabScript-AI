# GeneRead QIAact Lung DNA UMI Panel Kit: Adapter Ligation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung DNA UMI Panel Kit

## Description
This protocol automates the second part of a seven part protocol for the [GeneRead QIAact Lung DNA UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the Adapter Ligation part described in the [GeneRead QIAact Lung DNA UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=94ab92d2-1918-4388-989b-4cefa8eed203&lang=en).

* Part 1: [Fragmentation, End-repair and A-addition](https://protocols.opentrons.com/protocol/6d7fc3)
* Part 2: [Adapter Ligation](https://protocols.opentrons.com/protocol/6d7fc3-part-2)
* Part 3: [Cleanup of Adapter-ligated DNA with QIAact Beads.](https://protocols.opentrons.com/protocol/6d7fc3-part-3)
* Part 4: [Target Enrichment PCR](https://protocols.opentrons.com/protocol/6d7fc3-part-4)
* Part 5: [Cleanup of Target Enrichment PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-5)
* Part 6: [Universal PCR Amplification.](https://protocols.opentrons.com/protocol/6d7fc3-part-6)
* Part 7: [Cleanup of Universal PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-7)

Explanation of complex parameters below:

* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `P300 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `P20 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.

---

### Modules

* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware

* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96 Well 100 uL PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)

### Pipettes

* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

### Reagents

* [GeneRead QIAact Lung DNA UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/)

---

### Deck Setup

* The example below illustrates the starting deck layout for Part 2 (Adapter Ligation).
  ![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/6d7fc3-part-2-layout.png)

### Reagent Setup

* Slot 2: Empty 0.2 mL PCR Tubes in 96 Well Aluminum Rack

* Slot 3: **Red**: Adapters (up to 12, 1 for each sample) **Blue**: Ligation Reaction Master Mix

**Ligation Buffer**: B6

**DNA Ligase**: C6

**Ligation Solution** D6

---

### Protocol Steps
1. Pre-Cool Thermocycler and Temperature Module to 4°C.
2. Prepare and place reagents on the temperature module.
3. Mix Ligation Reaction Master Mix 10 times with 50 uL.
4. Transfer 2.8 uL of Adapters to separate PCR Tubes in Slot 2.
5. Transfer 25 uL of each fragmentation, end-repair and A-addition product into each 0.2 mL PCR tube(s) which contains an adapter
6. Add 22.2 uL of ligation master mix to each 0.2 mL PCR tube(s) and mix gently by pipetting up and down 7 times with a pipet set to 25 uL.
7. Centriduge the PCR tubes and place on ice. Add a new PCR plate in the thermocycler.
8. Set thermocycler to 20°C.
9. Return PCR tubes to aluminum block in Slot 2.
10. Transfer reaction mixture from PCR tubes to PCR plate in thermocycler.
11. Incubate reaction for 15 minutes at 20°C.
12. Protocol Complete!

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
6d7fc3-part-2
