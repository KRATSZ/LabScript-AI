# GeneRead QIAact Lung DNA UMI Panel Kit: Fragmentation, End-repair and A-addition

### Author

[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung DNA UMI Panel Kit

## Description

This protocol automates the first part of a seven part protocol for the [GeneRead QIAact Lung DNA UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the Fragmentation, End-repair and A-addition part described in the [GeneRead QIAact Lung DNA UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=94ab92d2-1918-4388-989b-4cefa8eed203&lang=en).

* Part 1: [Fragmentation, End-repair and A-addition](https://protocols.opentrons.com/protocol/6d7fc3)
* Part 2: [Adapter Ligation](https://protocols.opentrons.com/protocol/6d7fc3-part-2)
* Part 3: [Cleanup of Adapter-ligated DNA with QIAact Beads.](https://protocols.opentrons.com/protocol/6d7fc3-part-3)
* Part 4: [Target Enrichment PCR](https://protocols.opentrons.com/protocol/6d7fc3-part-4)
* Part 5: [Cleanup of Target Enrichment PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-5)
* Part 6: [Universal PCR Amplification.](https://protocols.opentrons.com/protocol/6d7fc3-part-6)
* Part 7: [Cleanup of Universal PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-7)

Explanation of complex parameters below:

* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `Samples Labware Type`: The starting samples can be placed in either NEST 2.0 mL tubes on the Opentrons Tube Rack OR in a 96 Well Plate.
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

* The example below illustrates the deck layout when the samples are placed in 1.5 mL Screwcap tubes in an Opentrons Tube Rack.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/6d7fc3_deck_layout.png)

### Reagent Setup

**Samples Setup Options (Either Tubes or Plate)**

Samples should be loaded going down the column first.

* Samples (1.5 mL Tubes): Slot 2

![Samples Tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_tubes.png)

* Samples (96 Well NEST-100 uL PCR Plate): Slot 2

![Samples Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/samples_plate.png)

**Temperature Module Reagent Setup**

**Master Mix Tube**: A1

**Fragmentation Enzyme Mix**: B1

**Fragmentation Buffer**: A2

**FERA**: B2

---

### Protocol Steps

1. Pre-Cool Thermocycler and Temperature Module to 4°C.
2. Prepare and place reagents on the temperature module.
3. Transfer 4 uL of DNA to PCR Plate on Thermocycler (This is performed for each sample). Change tips for each sample.
4. Thoroughly mix the master mix 10 times with a volume of 50 uL.
5. Transfer 16 uL of Master Mix to each reaction well on PCR plate on Thermocycler. Mix 10 times with a volume of 10 uL. Change tips for each sample.
6. Transfer 5 uL of Fragmentation Enzyme Mix to Thermocycler Reaction Plate. Change tips for each sample.
7. Set Thermocycler Lid temperature to 103°C
8. Begin thermocycler profile: 4°C for 1 minute, 32°C for 24 minutes, 72°C for 30 minutes.
9. Set and hold Thermocycler block temperature at 4°C.
10. Protocol completed!

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
6d7fc3
