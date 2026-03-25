# GeneRead QIAact Lung RNA Fusion UMI Panel Kit: Target Enrichment PCR

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung RNA Fusion UMI Panel Kit

## Description
This protocol automates the seventh part of a ten part protocol for the [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the Target Enrichment PCR part described in the [GeneRead QIAact Lung RNA Fusion UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=1a71d98a-c45c-44fa-b4af-874cd1d2b61f&lang=en).

* Part 1: [GeneRead QIAact Lung RNA Fusion UMI](https://protocols.opentrons.com/protocol/111210)
* Part 2: [Reverse transcription](https://protocols.opentrons.com/protocol/111210-part-2)
* Part 3: [Second strand synthesis](https://protocols.opentrons.com/protocol/111210-part-3)
* Part 4: [End repair / dA tailing](https://protocols.opentrons.com/protocol/111210-part-4)
* Part 5: [Adaptor ligation](https://protocols.opentrons.com/protocol/111210-part-5)
* Part 6: [Cleanup of Adapter-ligated DNA with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-6)
* Part 7: [Target Enrichment PCR](https://protocols.opentrons.com/protocol/111210-part-7)
* Part 8: [Cleanup of Target Enrichment PCR with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-8)
* Part 9: [Universal PCR Amplification](https://protocols.opentrons.com/protocol/111210-part-9)
* Part 10: [Cleanup of Universal PCR with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-10)


Explanation of complex parameters below:
* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
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
* [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936)

---

### Deck Setup
* The example below illustrates the starting deck layout for Part 4 (Target Enrichment PCR).
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/6d7fc3-part-4-layout.png)

### Reagent Setup

* Slot 2: PCR Tubes with DNA Library from Part 3

* Slot 3: **Red**: Forward Target Enrichment Master Mix (A1) **Blue**: Reverse Target Enrichment Master Mix (B1)

* Thermocycler: Empty NEST 100 uL PCR Plate

---

### Protocol Steps
1. Pre-Cool Temperature Module to 4°C.
2. Mix both Forward and Reverse Enrichment Master Mixes
3. Transfer reactions from PCR Tubes to PCR Plate in thermocycler
4. Begin Thermocycler Process with parameters below.

Lid Temperature: 103°C

95°C - 15 minutes - 1 cycle

95°C - 15 seconds - 8 cycles

68°C - 10 minutes - 8 cycles

72°C - 5 minutes - 1 cycle

4°C - 5 minutes - 1 cycle

4°C - Hold

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
111210-part-7