# PB Trial (Plate Filling)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the addition of three different reagents to 96-well plate(s) with the p20 8-channel pipette.</br>
</br>
First, 10µL of Reagent 1 (Polymixin B 256) will be added to columns 1-6 of each plate. Next, 10µL of Reagent 2 (Polymixin B 128) will be added to columns 6-12 of each plate. Finally, 10µL of Reagent 3 (Growth Media Gamma) will be added to all of the wells.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette) (on the right mount)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* HiMic 96-Well Plates, 400µL
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 11: [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)</br>
A1: Reagent 1 (Polymixin B 256)</br>
A2: Reagent 2 (Polymixin B 128)</br>
A3: Reagent 3 (Growth Media Gamma)</br>
</br>
Slot 10: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slots 1-9: HiMic 96-Well Plates, 400µL</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Plates**: Specify the number of plates to fill during the protocol.




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
1d37e5
