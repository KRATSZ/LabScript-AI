# Visby Test without Pooling p1000

### Author
[Opentrons](https://opentrons.com/)

### Partner
[BasisDx](https://www.basisdx.org/)



## Categories
* Sample Prep
	* Aliquoting

## Description
This flexible protocol automates the transferring of samples in 12mL tubes to dilution buffer, then to Visby device for rapid Covid testing.</br>
</br>

---
</br>
**Protocol Steps**</br>
1. The protocol begins by transferring (up to 5) samples from row A in slot 2 to A1, A3, A5, C1 and C3 (in that order) in slot 5, containing dilution buffer.
2. Once all samples are transferred to dilution buffer, *total volume of samples* will be added from slot 5 to Visby.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0.0 or later)](https://opentrons.com/ot-app/)
* [P1000 Single-Channel GEN2](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 1000µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [Visby Device with Adapter](https://www.visbymedical.com/covid-19-test/)
* Custom Tube Rack with 12mL Tubes

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)
</br>
**Deck Layout**</br>
</br>
**Slot 1**: [Opentrons 1000µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)</br>
</br>
**Slot 2**: Custom Tube Rack with 12mL Tubes, containing samples in row A</br>
</br>
**Slot 5**: Custom Tube Rack with 12mL Tubes, cotaining dilution buffer in A1, A3, A5, C1, and C3 (depending on the number of samples)</br>
</br>
**Slot 7**: [Visby 3](https://www.visbymedical.com/covid-19-test/)</br>
</br>
**Slot 8**: [Visby 4](https://www.visbymedical.com/covid-19-test/)</br>
</br>
**Slot 9**: [Visby 5](https://www.visbymedical.com/covid-19-test/)</br>
</br>
**Slot 10**: [Visby 1](https://www.visbymedical.com/covid-19-test/)</br>
</br>
**Slot 11**: [Visby 2](https://www.visbymedical.com/covid-19-test/)</br>
</br>
</br>
Explanation of adjustable parameters below:
* `P1000 Single GEN2 Mount`: Select which mount (left, right) the pipette is attached to.
* `Sample Volume (µL)`: Specify the volume (in µL) that should be transferred to the Visby. This volume will be transferred to the dilution buffer, before being transferred to the Visby.
* `Number of Samples`: Select the number of samples to test (1-5).


### Robot
* [OT-2](https://opentrons.com/ot-2)

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
115d98
