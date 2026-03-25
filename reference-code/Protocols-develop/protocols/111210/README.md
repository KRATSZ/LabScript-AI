# GeneRead QIAact Lung RNA Fusion UMI Panel Kit: First strand cDNA synthesis

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung RNA Fusion UMI Panel Kit

## Description
This protocol automates the first part of a ten part protocol for the [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the First strand cDNA synthesis part described in the [GeneRead QIAact Lung RNA Fusion UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=1a71d98a-c45c-44fa-b4af-874cd1d2b61f&lang=en).

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
* `Samples Labware Type`: The starting samples can be placed in either 1.5 mL tubes on the Opentrons Tube Rack OR in a 96 Well Plate.
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
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

### Reagents
* [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936)

---

### Deck Setup
* The example below illustrates the deck layout when the samples are placed in 1.5 mL Screwcap tubes in an Opentrons Tube Rack.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/111210/111210_layout.png)

### Reagent Setup
**Samples Setup Options (Either Tubes or Plate)**

Samples should be loaded going down the column first.
* Samples (1.5 mL Tubes): Slot 2

![Samples Tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_tubes.png)

* Samples (96 Well NEST-100 uL PCR Plate): Slot 2

![Samples Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_plate.png)

**Reagent Setup**

**Slot 5**: RP Primer Tube (A1, Red)

---

### Protocol Steps
**Note:** The protocol assumes the samples have been diluted to 20 ng/uL.
1. Pre-heat Thermocycler to 65°C with a heated lid at 103°C.
2. Cool the temperature module to 4°C.
3. Place Aluminum block with PCR plate on top of the temperature module.
4. Transfer 5 uL of RNA to PCR plate on temperature module.
5. Add 1 uL of RP Primer to RNA samples on PCR plate.
6. Mix 7 times with a volume of 4 uL.
7. Centrifuge PCR plate with samples for 15 seconds.
8. Place PCR plate in the thermocycler.
9. Incubate at 65°C for 5 minutes.
10. Remove the PCR plate from the thermocycler and place on ice OR temperature module for a few minutes.
11. Briefly centrifuge before the next protocol.

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
111210