# Nucleic Acid Purification with Magnetic Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Purification


## Description
This protocol performs a nucleic acid purification with the Opentrons magnetic module.

Lysis buffer is added to sample and mixed. The subsequent lysate is then added to magnetic beads with isopropanol. After mixing, the Opentrons magnetic module is engaged and supernatant is removed and returned to reservoir. Two washes are then performed using wash and elution buffer, respectively. The final elute is transferred to an Opentrons 96-Well Aluminum Block plate. 


---
![Materials](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)
* [Opentrons 200µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons Magnetic Module](https://opentrons.com/modules/magnetic-module/)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_generic_pcr_strip_200ul?category=aluminumBlock)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)
* YDP 96-Well Square Well-Plate 2200ul



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL

Slot 2: Opentrons 96 Filter Tip Rack 200 µL

Slot 3: Opentrons 96 Filter Tip Rack 200 µL

Slot 6: YDP 96-Well Square Well-Plate 2200ul with Magnetic Module

Slot 11: NEST 1 Well Reservoir 195 mL


</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Distance From Side of well**: Specify the distance from the well wall the pipette will aspirate from. The pipette will aspirate from this distance on the well wall opposite that of the magnetic beads. An input value of 4.05 returns the center of the well.
* **Number of Plates**: Specify the mount side for the P300 Multi Channel Pipette.

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
65ed01
