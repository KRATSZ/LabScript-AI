# Plate Filling with Custom 384-Well Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the filling of a specialized 384-well (rotated 90 degrees and takes up two slots). Using a 96-well plate containing the reagents, the p20 will aspirate 20µL from the 96-well plate and dispense 10µL into the 384-well plate, swapping tips each time the the p20 moves to another column (different reagents) until the 384-well plate is filled.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 Multi-Channel Pipette (attached to right mount)](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 20µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* 384-Well Plate with Custom Adapter


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 1: [Opentrons 20µL Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 5: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
*Reagent Locations*</br>
* Reagent 1: B1 (40µL), H11 (160µL), and H12 (160µL)
* Reagent 2: B2 (40µL), G11 (160µL), and G12 (160µL)
* Reagent 3: A1 (40µL), F11 (160µL), and F12 (160µL)
* Reagent 4: B3 (40µL), E11 (160µL), and E12 (160µL)
* Reagent 5: B4 (40µL), D11 (160µL), and D12 (160µL)
* Reagent 6: A3 (40µL), C11 (160µL), and C12 (160µL)
* Reagent 7: B6 (40µL), B11 (160µL), and B12 (160µL)
* Reagent 8: B5 (40µL), A11 (160µL), and A12 (160µL)
* Reagent 9: D1-D8 + B8 (40µL)
* Reagent 10: C1-C8 + B7 (40µL)
</br>
Slot 3/6: 384-Well Plate with Custom Adapter

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
387961
