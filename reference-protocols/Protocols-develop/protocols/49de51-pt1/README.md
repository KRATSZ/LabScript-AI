# MagMAX Plant DNA Isolation Kit [1/2] Disrupt Tissue

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA


## Description
This protocol automates the ThermoFischer MagMAX Plant DNA Isolation Kit on up to 192 samples (2 plates of 96). The entire workflow is broken into 2 different protocols. This is part 1, disrupting the tissue.</br>
</br>
In this protocol, 590µL of buffer (combination of 500µL lysis Buffer A, 70µL of Lysis Buffer B, and 20µL of RNase A) is added to each well. The user is then prompted to remove the plate(s) for off deck vortexing/shaking and incubation. Once incubation is complete, the user returns the plate(s) to the deck and the robot will add 130µL of the precipitation solution. After one final incubation off the robot and a spin down, 400µL of supernatant is transferred to a deep well plate. The 400µL sample can be stored or purified with part 2 of the protocol.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p300 Multi-Channel Pipette (attached to right mount)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* 96-Deep Well Plate (such as the [OMNI 96-Well Deep Well Plate with Ceramic Beads](https://www.omni-inc.com/consumables/well-plates/2-pack-96-well-plate-1-4mm-ceramic.html))
* [MagMAX™ Plant DNA Isolation Kit](https://www.thermofisher.com/order/catalog/product/A32549#/A32549)
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 1: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
* A1: Precipitation Solution, 13.5mL (for Plate 1)
* A2: Precipitation Solution, 13.5mL (for Plate 2)


Slot 2: [OMNI 96-Well Deep Well Plate with Ceramic Beads](https://www.omni-inc.com/consumables/well-plates/2-pack-96-well-plate-1-4mm-ceramic.html) containing sample (Plate 1)</br>
</br>
Slot 3: [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) (empty, for Plate 1 supernatant)</br>
</br>
Slot 4: [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)</br>
For each plate, the following should be added:
* Lysis Buffer A, 52mL
* Lysis Buffer B, 4.160mL
* RNase A, 2.080mL


Slot 5: [OMNI 96-Well Deep Well Plate with Ceramic Beads](https://www.omni-inc.com/consumables/well-plates/2-pack-96-well-plate-1-4mm-ceramic.html) containing sample (Plate 2)</br>
</br>
Slot 6: [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) (empty, for Plate 2 supernatant)</br>
</br>
Slot 7: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 10: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 11: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
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
49de51-pt1
