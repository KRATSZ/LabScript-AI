# Adding Developer Solution to 216 Well Cartridge Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol transfers a specified volume of developer solution into reservoir cartridges within a custom 216-well plate. The developer solution is aspirated from a Nest 195mL reservoir, then distributed to the 216-well plate down by column. Transfers are distributed in chunks of 3 between the reservoir and plate, with a delay and blow out step for viscous liquid considerations. Extra developer solution is aspirated to ensure that each cartridge receives adequate distribution.


---
![Materials](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Nest 1-Well Reservoir 195 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-1-well-reservoir-195-ml)
* Invoy 216-Well Cartridge Plate
* Invoy Canisters with Fibrous Reservoir



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1, 2, 4, 5, 7, 8, 10, 11: Invoy 216-Well Cartridge Plate

Slot 6: Opentrons 96 Tip Rack 300 µL

Slot 9: Nest 1-Well Reservoir 195 mL




</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify the number of samples in your protocol run.
* **Dispense Height Above Cartridge**: Specify the height (mm) above the cartridge the pipette will dispense liquid
* **Dispense Volume**: Specify the volume (µL) of developer solution dispensed into each cartridge
* **Dispense Flow Rate**: Specify the rate (µL/sec) at which the pipette will aspirate solution into each cartridge
* **Dispense Flow Rate**: Specify the rate (µL/sec) at which the pipette will dispense solution into each cartridge
* **Aspirate Delay Time**: Specify the time to delay after each aspiration (in seconds)
* **Dispense Delay Time**: Specify the time to delay after each dispense (in seconds)
* **P300 Single GEN2 Mount**: Specify the mount side for the P300 Single GEN2 pipette

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package containing the custom labware definitions for the reservoir and plate.
2. Upload the labware definition in the [OT App](https://opentrons.com/ot-app). For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7f0f89
