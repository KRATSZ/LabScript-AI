# SPRI 3

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Extraction

## Description

Links:  
* [SPRI 1 & 2](./3607d5-2)
<br />
<br />
* [PCR2 Setup](./3607d5)
<br />
<br />
* [SPRI 3](./3607d5-3)
<br />
<br />
* [Normalization and Pooling](./3607d5-4)
<br />
<br />
* [Rerack](./3607d5-5)

The protocol is broken down into 4 main parts:
* binding buffer addition to samples
* bead wash 2x using magnetic module
* final elution to chilled PCR plate

Samples should be loaded on the magnetic module in an Abgene Midi plate. For reagent layout in the 2 12-channel reservoirs used in this protocol, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 11) to the elution PCR plate (temperature module, slot 3). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

---

### Modules
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Abgene Midi 96 Well Plate 800 µL
* Amplifyt 96 Well Plate 200 µL
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [Opentrons 20µl and 300µl Tipracks](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Multi GEN2 Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup
* blue: samples  
* green: binding beads  
* pink: EtOH  
* purple: RSB
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3607d5/deck23.png)

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
3607d5
