# PCR2 Setup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

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

In this protocol, indexes are transferred to their corresponding wells in a PCR plate containing samples. Then, PCR2 buffer is added to each sample and mixed using fresh tips for each transfer.

---

### Labware
* Abgene Midi 96 Well Plate 800 µL
* Amplifyt 96 Well Plate 200 µL
* [Opentrons 20µl and 300µl Tipracks](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Multi GEN2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* green: PCR2 buffer  
* blue: samples  
* pink: UDI
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3607d5/deck1.png)

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
