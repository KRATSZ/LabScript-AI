# Visby Test with Pooling p1000

### Author
[Opentrons](https://opentrons.com/)

### Partner
[BasisDx](https://www.basisdx.org/)



## Categories
* Sample Prep
	* Pooling

## Description
This flexible protocol automates the pooling of samples in 12mL tubes and the transfer of pooled samples to Visby device for rapid Covid testing.</br>
</br>

---
</br>
**Protocol Steps**</br>
1. The protocol begins by pooling samples (1-5) from Tube Racks in slots 2 and 3 into tubes in slot 5.
2. Once all samples are pooled appropriately, *total volume of pooled samples* will be added from pooled sample to Visby.

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
![full deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3955db/Visby+OT2+Maximum.png)
</br>
</br>
Explanation of adjustable parameters below:
* `P1000 Single GEN2 Mount`: Select which mount (left, right) the pipette is attached to.
* `Total Volume of Pooled Samples`: Specify the volume (in µL) that should be transferred to the Visby. This volume will be divided by the `Number of Samples per Pool` to determine how much volume from each individual sample when creating the pools. Example: if this is set to 500 and there are 5 samples per pool, 100µL will be transferred from each individual sample to the pooled sample tube, then 500µL of the pooled volume will be added to the Visby.
* `Number of Visbys`: Select the number of Visbys (1-6).
* `Number of Samples per Pool`: Select the number of samples to pool into one tube (2-5).


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
3955db
