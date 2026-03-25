# Verogen ForenSeq DNA Signature Prep Kit Part 3/5: Library Purification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Verogen ForenSeq DNA Signature Prep Kit

## Description

Links:  
* [Part 1](./17d210)
<br><br />
* [Part 2](./17d210-part-2)
<br><br />
* [Part 3](./17d210-part-3)
<br><br />
* [Part 4](./17d210-part-4)
<br><br />
* [Part 5](./17d210-part-5)

This custom Library Purification protocol is part 3/5 of the [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE). The protocol is broken down into 4 main parts:
* binding buffer addition to samples
* bead wash 2x using magnetic module
* final elution to chilled PCR plate

Samples should be loaded on the magnetic module in an Abgene Midi plate. For reagent layout in the 2 12-channel reservoirs used in this protocol, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 11) to the elution PCR plate (temperature module, slot 3). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

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

### Reagents
* [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE)

---

### Deck Setup
* green: samples
* blue: binding bead buffer
* pink: 80% EtOH  
* purple: elution buffer
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/17d210/deck3-2.18.24+AM.png)

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
17d210
