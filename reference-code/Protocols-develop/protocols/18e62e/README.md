# PCR Prep with 384-Well Plate and Temperature Module

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates a Multiplex LDT 384-Well Plate PCR prep. Using up to four KingFisher 96-Well Plates as inputs and an [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) to keep reagents cool, this protocol transfers water, primer/probes, and master mix to necessary wells in 384-Well Plate before transferring samples from the KingFisher plates.

This protocol is still a work in progress and will be updated.

**Update 2021-10-25:** A new parameter was added (*Only Transfer Samples*) that will skip the addition of reaction mix components and use of the temperature module; instead, simply transferring samples from 96-well plates to 384-well plate.


Explanation of complex parameters below:
* **Plate 1 Number of Samples**: Specify the number of samples in Plate 1 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 2 Number of Samples**: Specify the number of samples in Plate 2 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 3 Number of Samples**: Specify the number of samples in Plate 3 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Plate 4 Number of Samples**: Specify the number of samples in Plate 4 (up to 96). The plate can be skipped by setting this value to 0 (zero).
* **Pipette Mount**: Select which mount the [P20 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) is attached to.
* **Used Tip Location**: Select where used tips should be dropped after transferring samples. *Empty Tip Rack* is recommended due to space constraints in the waste bin.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [KingFisher 96-Deepwell Plate](https://www.thermofisher.com/order/catalog/product/A48305?SID=srch-hj-a48305#/A48305?SID=srch-hj-a48305)
* [MicroAmp™ EnduraPlate™ Optical 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4483321?SID=srch-srp-4483321#/4483321?SID=srch-srp-4483321KF96)
* [Opentrons 96-Well Aluminum Block + PCR Strips (200µL)](https://labware.opentrons.com/opentrons_96_aluminumblock_generic_pcr_strip_200ul?category=aluminumBlock)

### Pipettes
* [P20 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* Water
* Primer/Probe Mix
* Master Mix

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/18e62e/18e62e_deck.png)

### Reagent Setup
![Reagent Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/18e62e/18e62e_reagents.png)
</br>
**Water**: These PCR strips should be loaded in columns 1-4; each column corresponds to that sample plate. For a full sample plate, the PCR strip should contain at least 102µL in each tube (we recommend a 10% overage).
**Primer/Probe Mix**: This PCR strip should be loaded in column 6. For 384 samples, 72µL is needed in tube of the strip.
**Master Mix**: These PCR strips should be loaded in columns 8 and 9; each column corresponds to two sample plates. For a full sample plate, the PCR strip should contain at least 120µL in each tube (we recommend a 10% overage).
</br>
Samples from Plate 1 and 2 will fill every other column beginning with column A; samples from Plate 1 will begin in column 1, samples from Plate 2 will begin in column 13. Samples from Plate 3 and 4 will fill every other column beginning with column B; samples from Plate 3 will begin in column 1, samples from Plate 4 will begin in column 13. Please see illustration below for what the 384-Well Plate would look like with the sample plates depicted above.
![384-well plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/50c11b/50c11b_384wellplate.png)

---

### Protocol Steps
1. The pipette will pick up a column of tips and transfer 8.5µL of water to all destination wells in the 384-Well Plate, then dispose of tips.
2. The pipette will pick up a column of tips and transfer 1.5µL of primer/probe mix to all destination wells in the 384-Well Plate, then dispose of tips.
3. The pipette will pick up a column of tips and transfer 5µL of master mix to all destination wells in the 384-Well Plate, then dispose of tips.
4. For each column of samples in Plate 1, the pipette will pick up tips.
5. Samples will be mixed, then transferred to the 384-well plate (Rows A/C/E..., Columns 1-12) and mixed.
6. Tips will be disposed of in the waste bin.
7. For each column of samples in Plate 2, the pipette will pick up tips.
8. Samples will be mixed, then transferred to the 384-well plate (Rows A/C/E..., Columns 13-24) and mixed.
9. Tips will be disposed of in empty tip slots used for Plate 1.
7. For each column of samples in Plate 3, the pipette will pick up tips.
10. Samples will be mixed, then transferred to the 384-well plate (Rows B/D/F..., Columns 1-12) and mixed.
11. Tips will be disposed of in empty tip slots used for Plate 2.
12. For each column of samples in Plate 4, the pipette will pick up tips.
13. Samples will be mixed, then transferred to the 384-well plate (Rows B/D/F..., Columns 13-24) and mixed.
14. Tips will be disposed of in empty tip slots used for Plate 3.
15. End of the protocol.


### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
18e62e
