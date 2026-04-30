# Capping Assay: Steps 1-2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
    * Normalization

## Description

Links:
* [Steps 1-2 (annealing preparation and digestion)](./7062c9)
* [Steps 3-6 (extraction)](7062c9-2)

This is a flexible normalization protocol accommodating sample annealing preparation and digestion pre- and post-PCR. Normalization parameters should be input as a .csv file below, and should be formatted as shown in the following template:

```
sample conc. (mg/ml),sample volume (µl),water volume (µl),buffer 1 (µl),probe volume (µl),probe tube location (C1-D6),total volume (µl)
1,40,50,10,5,A3,105
2.2,18.2,71.8,10,5,A3,105
2.03,19.7,70.3,10,5,A4,105
```

For sample traceability and consistency, samples are mapped directly from the sample plate (slot 1) to the final normalized plate (slot 2). Sample plate well A1 is transferred to normalized plate A1, Sample plate well B1 to normalized plate B1, ..., D2 to D2, etc.

---

### Labware
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://labware.opentrons.com/nest_96_wellplate_100ul_pcr_full_skirt)
* [Opentrons 24 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [NEST 1.5 mL Screwcap Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-1-5-ml-sample-vial) or equivalent
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 96 Filter Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)

### Pipettes
* [P300 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P20 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup
This example starting deck state shows the layout for 24 samples:  
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7062c9/deck1-4.png)

* green on sample tuberack: starting samples
* blue on reagent reservoir: water
* pink on buffer + probe tuberack: buffer
* purple on buffer + probe tuberack: protease
* orange buffer + probe tuberack: available spots for probes

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
7062c9
