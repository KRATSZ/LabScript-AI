# Protein Purification with Magnetic NI Resin

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Purification


## Description
This protocol automates the purification of samples, using magnetic NI resin, ThermoFisher B-PER reagent, and homemade buffers.</br>
</br>
This protocol requires the user to perform some off-deck steps (centrifuge) and replace tips midway. Both actions will be prompted by flashing lights a message in the Opentrons app.</br>
</br>
This protocol uses custom labware definitions for the NEST deep well plate and the Chrom Tech 96-well filter plate. When downloading the protocol, the labware definitions (a JSON file) will be included for use with this protocol. For more information on using custom labware on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols)


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* (6) [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* (4) [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* NEST Deep Well Plate
* Chrom Tech 96-Well Filter Plate
* Samples
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Part 1: B-PER Addition, Incubation, and Transfer**</br>
Slot 10: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 11: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 8: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 9: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 7: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 4: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
* A1: B-PER Reagent
* A3: Magnetic NI Resin
* A5: Wash Buffer (first wash)
* A7: Wash Buffer (second wash)
* A9: Elution Buffer
</br>

Slot 5: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 1: NEST Deep Well Plate with Samples
</br>
*This setup will be sufficient for the protocol up through the addition of the second wash buffer. After the second addition of the wash buffer, the OT-2 will pause and prompt the user to replace the tips in slots 8 and 9, and ensure that the remaining plates are in place (they can be loaded earlier if wanted)*
</br>
**Part 2: 2nd Wash and Elution (in addition to previous labware...)**</br>
Slot 6: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 2: [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 3: Chrom Tech 96-Well Filter Plate
</br>
</br>


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
13fd88
