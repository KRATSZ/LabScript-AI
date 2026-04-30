# Pooling Samples and Distribution to Cepheid

### Author
[Opentrons](https://opentrons.com/)

### Partner
[BasisDx](https://www.basisdx.org/)



## Categories
* Sample Prep
	* Cepheid

## Description
This protocol automates the pooling of samples and distribution to Cepheid for rapid Covid-19 diagnostics.

The protocol begins by pooling samples in groups of 10. Once pooled, the pooled samples are mixed and transferred to the Cepheid device on a custom adapter containing the Cepheid device on the deck of the OT-2.

Explanation of complex parameters below:
* **Number of Samples**: Specify the number of samples to run (in groups of 10).
* **P1000 Mount**: Specify which mount the [P1000 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) is attached to

---

### Labware
* [Opentrons 15-Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* 12mL Tubes
* Cepheid

### Pipettes
* [P1000 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cepheid/cepheid_deck.png)


---

### Protocol Steps
1. For each grouping of samples (10), the [P1000 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) will pick up a tip, transfer 62µL of sample (with 50µL air gap) to destination well (samples 1-10 --> A1; samples 11-20 --> A5; samples 21-30 --> C1), and drop used tip in the waste bin.
2. The [P1000 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) will mix the pooled sample and then transfer 300µL of pooled sample to the corresponding Cepheid device.
3. This process will repeat for each group of 10 samples, up to 30 samples.
4. End of the protocol.

### Process
1. Input your protocol parameters above.
2. Download your protocol bundle containing protocol and custom labware; unzip bundle.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
cepheid
