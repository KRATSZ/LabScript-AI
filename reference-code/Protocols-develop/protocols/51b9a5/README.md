# Agar Plating

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Agar Plating

## Description

This protocol transfers up to 96 samples to up to 9 different source plates. Samples are transferred to their corresponding positions in the agar plates. Tips are changed between transfers of different samples to avoid contamination. The user has the option to puncture the agar plate before dispensing the sample on the agar.

---

### Labware
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* Nunc rectangular agar plates

### Pipettes
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or [P20 Multi GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

---

### Deck Setup
* slot 1: 20µl tiprack
* slot 2: source plate
* slots 3-11: agar plates

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
51b9a5
