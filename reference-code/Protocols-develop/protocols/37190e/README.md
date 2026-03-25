# Cell Culture

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sterile Workflows
	* Cell Culture

## Description

This protocol performs a custom cell culture assay on up to 8 flat well plates. Please see [these instructions](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37190e/opentrons_media_table.xlsx) for the exact transfer scheme.

---

### Labware
* [Corning 96 Well Plate 360 µL Flat, 3650](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [Opentrons 10 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/) with [NEST 4x50 mL](https://shop.opentrons.com/nest-50-ml-centrifuge-tube/), [6x15 mL Conical](https://shop.opentrons.com/nest-15-ml-centrifuge-tube/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/37190e/deck.png)  

Tuberack on slot 9:
* tube A1: drug A
* tube A2: drug B
* tube A3: media

---

### Protocol Steps
1. Drug A is transferred to the bottom of all wells.
2. Drug B is transferred to the left of all wells.
2. Media is transferred to the right of all wells to bring to total volume of 100ul.

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
37190e
