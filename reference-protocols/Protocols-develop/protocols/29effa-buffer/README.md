# Lyra Direct Covid-19 Buffer Distribution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the distribution of process buffer from the [Lyra Direct SARS-CoV-2 Assay](https://www.quidel.com/molecular-diagnostics/lyra-direct-sars-cov-2-assay) into a 96-well format.</br>
Using an [Opentrons P300 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), this protocol will transfer 400µL of process buffer from a 12-well reservoir to the specified number of wells in a 96-well plate.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 8-Channel Pipette, GEN2](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 300µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* Eppendorf 96-Well Plate
* [Lyra Direct SARS-CoV-2 Assay Kit](https://www.quidel.com/molecular-diagnostics/lyra-direct-sars-cov-2-assay)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 1: [Opentrons 300µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 4: Eppendorf 96-Well Plate</br>
</br>
Slot 7: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
**Process Buffer Loading:** Each column of the reservoir can contain enough buffer for up to 24 wells. Ex: if running 96 wells, columns 1-4 should be loaded with buffer</br>
</br>


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol bundle.
2. Upload [custom labware definition](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols), if needed.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
29effa-buffer
