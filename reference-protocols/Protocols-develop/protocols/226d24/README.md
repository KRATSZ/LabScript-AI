# PCR Set-Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep


## Description
This protocol automates a PCR prep involving uniquely barcoded forward primers and can accommodate 1-96 samples.</br>
</br>
The protocol begins with the creation of a reaction mix (water, mastermix, and reverse primers) and distribution of that reaction mix. Following this, uniquely barcoded forward primers are transferred to corresponding wells of the PCR plate containing the reaction mix. Finally, samples are transferred in a similar manner from a deep well plate to the PCR plate.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons P20 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tip Rack(s)](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* KingFisher Deep Well Plate, 2mL
* PlateOne Deep Well Plate, 1mL
* Samples
* Reagents (Water, Mastermix, Primers)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


**Deck Layout**</br>
</br>
Slot 1: KingFisher Deep Well Plate containing Samples</br>
</br>
Slot 2: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 3: [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 4: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) (clean and empty)</br>
</br>
Slot 5: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for reagents)</br>
A1: Water (26µL per sample, plus overage)</br>
A2: Mastermix (20µL per sample, plus overage)</br>
A3: Reverse Primers (1µL per sample, plus overage)</br>
A4: Empty; will be used for reaction mix</br>
</br>
Slot 6: [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 7: PlateOne Deep Well Plate containing Forward Primers</br>
</br>



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
226d24
