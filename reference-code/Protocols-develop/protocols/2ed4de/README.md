# Ribogreen Assay - 2 Standards and up to 8 Samples

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Ribogreen Assay

## Description

Links:
* [Part 1](./2ed4de)
* [Part 2](./2ed4de-2)

This is a protocol for the Flu Ribogreen Assay protocol. Samples are aligned in the sample tuberack (slot 1) in the following order:
* A1 -> sample 1
* B1 -> sample 2
* C1 -> sample 3
* D1 -> sample 4
* A2 -> sample 5
* B2 -> sample 6
* C2 -> sample 7
* D2 -> sample 8

---

### Labware
* [Corning 96 Well Plate 360 µL Flat](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Corning®-96-well-Solid-Black-and-White-Polystyrene-Microplates/p/corning96WellSolidBlackAndWhitePolystyreneMicroplates)
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [NEST 2 mL 96-Well Deep Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [Opentrons 24 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with Eppendorf 1.5 mL Screwcap Tubes or equivalent
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 96 Filter Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)

### Pipettes
* [P300 Multi-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P1000 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup
This example starting deck state shows the layout for 8 samples:  
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2ed4de/deck4.png)

* green on sample tuberack: samples
* blue on reagent reservoir: working standard 1
* pink on reagent reservoir: assay buffer 1 (TE)
* purple on reagent reservoir: working standard 2
* orange on reagent reservoir: assay buffer 2 (TR)

---

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
2ed4de
