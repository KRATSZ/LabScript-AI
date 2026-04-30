# PCR Prep - Plate Filling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep


## Description
This protocol automates the creation of a PCR Plate with a variable number of samples.</br>
</br>
Using the [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [2mL Eppendorf tubes](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap?category=tubeRack), 20µL of pre-made master mix is added to PCR Plate. Following the addition of master mix to all necessary wells, 5µL of water is added for the negative control and 5µL of each sample is added to the other well(s).</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* Eppendorf 2mL Tubes
* Master Mix
* Negative Control (Water)
* Samples



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
**Slot 1**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) containing Samples (1-24)</br>
</br>
**Slot 2**: [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (Final PCR Plate)</br>
</br>
**Slot 3**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)</br>
A1: Master Mix</br>
D6: Negative Control (Water)</br>
</br>
**Slot 4**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) containing Samples (25-48)</br>
</br>
**Slot 7**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) containing Samples (49-72)</br>
</br>
**Slot 10**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) containing Samples (73-95)</br>
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify the number of samples to run (1-95).





### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol file.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
642c73
