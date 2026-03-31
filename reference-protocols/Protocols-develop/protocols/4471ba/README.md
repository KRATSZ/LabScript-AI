# Custom Plate Filling (Flipped)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates filling plates that have been turned 90-degrees on the deck. Using custom adapters, the P300 Multi-Channel Pipette is used to transfer a set volume (selected below) from a Beckman Coulter 8-Channel Reservoir to a Simport 96-Well Plate (on an adapter that allows the plate to be turned 90-degrees). The P300 Multi-Channel pipette picks up tips from an Opentrons Tip Rack (also on an adapter), by picking up 8/12 tips from the column (liquid transfer happens to 8/12 wells in column on plates) and then the last 4 tips in the column (for last 4/12 wells in columns on plates).
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 300µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* (2x) Simport 96-Well Plate, 1200µL
* Beckman Coulter 8-Channel Reservoir, 19mL
* Reagents

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


**Deck Layout**</br>
</br>
Slot 2/5: Simport 96-Well Plate, in adapter (Plate 1)</br>
</br>
Slot 8/11: Simport 96-Well Plate, in adapter (Plate 1)</br>
</br>
Slot 4/7: [Opentrons 300µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (in adapter)</br>
</br>
Slot 10: Beckman Coulter 8-Channel Reservoir with Reagents</br>
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **P300-Multi Mount**: Select which mount (left or right) the P300-Multi is attached to.
* **Transfer Volume (µL)**: Specify the volume (in µL) that should be transferred to each well.
* **Number of Columns to Fill (1-8)**: Specify the number of columns to fill in each plate.


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol.
2. Upload [custom labware definition](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols), if needed.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4471ba
