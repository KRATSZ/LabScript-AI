# Automated Sample Prep for GNA Octea

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Covid

## Description
This protocol automates GNA Octea prep. Using the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) and the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), all the reagents necessary for the sample prep are transferred to the samples and the samples are incubated on the [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) and [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck). Once all sample prep has been completed, the samples are transferred to a custom plate containing the labware needed to test the samples on the [GNA analyzer](https://www.gna-bio.com/products/).

This protocol is still a work in progress and will be updated.

**Update (06/07/2021)**: This protocol has been updated per conversation and has several modifications (slight), such as, changing the distribution of reagent to multi-dispense and allowing the temperature module to heat up while pipetting occurs.

**Update (06/10/2021)**: This protocol has been updated and now includes new mixing functions and incorporated air gaps.

Explanation of complex parameters below:
* **P300-Multi Mount**: Select which mount the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) is attached to.
* **P300-Single Mount**: Select which mount the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) is attached to.
* **Number of Samples**: Specify the number of samples to be run. Currently, 8 is the only number allowed.


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [NEST 96-Deep Well Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Bio-Rad 96-Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* Custom Plate for GNA Octea Chip

### Pipettes
* [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

### Reagents
* WB1
* RB1
* HB1
* MM Lyo
* MB Lyo

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/gna_octea/gna_deck_layout.png)

### Reagent Setup
[NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (Deck Slot 7)
* Well 1: WB1
* Well 3: HB1
* Well 12: Liquid Waste (Empty)

[NEST 96-Deep Well Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom) (Deck Slot 8)
* Column 1/A1-H1: Samples
* A12: RB1
* D11: MB Lyo
* D12: MM Lyo

---

### Protocol Steps
1. The [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) will heat to 90°C and the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) will engage.
2. The [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) will pick up a tip, transfer 360µL of HB1 to MB Lyo, mix and distribute 40µL of mixture to wells adjacent to wells containing samples in [NEST 96-Deep Well Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom).
3. The [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer HB1 to [NEST 96-Deep Well Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom) - 360µL to previous wells and 300µL to wells containing samples, changing tips between these steps.
4. Using the same tips from the previous step, the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer the sample+HB1 mixture to the adjacent wells, mix, and trash the tips.
5. Using a new set of tips, the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer 160µL to the first 5 columns of the [Bio-Rad 96-Well Plate sitting on the 96-Well Aluminum Block](https://labware.opentrons.com/opentrons_96_aluminumblock_biorad_wellplate_200ul?category=aluminumBlock) on top of the [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck).
6. The [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) will change its temperature from 90°C to 80°C. Once the desired temperature is reached, the protocol will delay for two minutes. At the conclusion of this delay/incubation, the [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) will change its temperature to 56°C. The [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will mix all of the samples on the [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) and after mixing, the [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) will deactivate.
7. Using the tips from the previous steps, the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will transfer the samples from the [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) to the corresponding wells of the Bio-Rad plate on the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck). The protocol will then delay for three minutes.
8. The [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up a new set of tips and lower the flow rate to remove the supernatant and discard in the liquid waste (Well 12 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)).
9. The [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up a new set of tips and will transfer WB1 to samples on the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck), mix, and recombine the samples in column 5.
10. The [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) will engage and the protocol will delay for three minutes. After the delay, the [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will remove supernatant from the sample wells and discard in the liquid waste.
11. The [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) will transfer 350µL RB1 to the well containing the MM Lyo, mix, and distribute 40µL to the sample wells on the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck).
12. The [P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette) will pick up a new set of tips and mix the samples in column 5 on the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) containing sample and RB1+MM Lyo.
13. For each well containing sample on the [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) (8), the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) will pick up a new tip and transfer to the corresponding well on the custom plate containing the GNA Octea Chip.


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
gna_octea
