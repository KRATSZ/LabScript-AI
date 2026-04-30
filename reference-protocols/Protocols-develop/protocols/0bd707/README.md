# Media Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Aliquoting

## Description
This protocol is a modified version of this [sample aliquoting protocol](https://develop.protocols.opentrons.com/protocol/53134e).</br>
</br>
With this version of the protocol, the user can specify the number of plates they would like to fill (up to 6). When run, the robot will transfer the specified volume two times (2x) to each tube, in each tube rack, and change tip after each liquid transfer.</br>
</br>
Please note that this protocol uses a custom labware definition for the tube rack (definition included with download). For more information regarding custom labware definition usage on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.17.0 or later)](https://opentrons.com/ot-app/)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml)
* [Opentrons P1000 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549142557)
* [Opentrons 96 Tip Rack 1000 µL](https://labware.opentrons.com/opentrons_96_tiprack_1000ul)
* 24-Tube Tube Rack plus Tubes

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Tube Racks**</br>
Load sequentially deck slots, in this order: *2, 3, 5, 6, 7, 8, 9*</br>
</br>
**Tip Racks**</br>
One tip rack is needed for every two tube racks. The tip racks should be loaded in deck slots: *1, 4*</br>
</br>
**Reagent Reservoirs**</br>
One reagent reservoir should be used for every three tube racks. The reservoirs should be loaded in deck slots: *11 (will be used first), 10*</br>

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of plates to process (1-6), the transfer volume (in µl), and the mount side for your P1000 GEN2 single-channel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0bd707
