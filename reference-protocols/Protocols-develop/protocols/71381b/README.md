# Zymo Quick DNA HMW + Labelling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Kit


## Description
This protocol automates the [Zymo Quick-DNA HMW MagBead Kit](https://www.zymoresearch.com/products/quick-dna-hmw-magbead-kit) with an additional labelling step that takes place before the purification.</br>
</br>
The parameter section below gives you the ability to select either the **Labelling** portion of the protocol or the **Purification** portion of the protocol (you can select both). During the labelling portion, MilliQ Water, CSB, M.Taql, MTC22, and Proteinase K are added to the samples and the samples incubate while on the Temperature Module. During the purification portion, the samples are purified using the Zymo MagBead Kit in conjunction with Opentrons Magnetic Module.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Temperatue Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P20 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons P300 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 20µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 300µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Zymo Quick-DNA HMW MagBead Kit](https://www.zymoresearch.com/products/quick-dna-hmw-magbead-kit)
* Reagents for Labelling
* Samples



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
**Slot 1**: [Opentrons Temperatue Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) on 96-Well Aluminum Block, containing samples in columns 1-4</br>
</br>
**Slot 2**: [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (Labelling Plate)</br>
Column 1: MTC22</br>
Column 3: CSB</br>
Column 5: M.Taql</br>
Column 7: Proteinase K</br>
</br>
**Slot 3**: [Opentrons 20µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Labelling)</br>
</br>
**Slot 4**: [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [Bio-Rad 96-Well PCR Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (empty)</br>
</br>
**Slot 5**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
Column 1: MilliQ Water</br>
Column 2: MagBeads</br>
Column 3: MagBinding Buffer</br>
Column 4: Wash Buffer 1</br>
Column 5: Wash Buffer 2</br>
Column 6: Elution Buffer</br>
</br>
**Slot 6**: [Opentrons 20µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Labelling)</br>
</br>
**Slot 7**: [Opentrons 300µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Purification)</br>
</br>
**Slot 8**: [Opentrons 300µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Purification)</br>
</br>
**Slot 10**: [Opentrons 300µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Purification)</br>
</br>
**Slot 11**: [Opentrons 20µL Tip Racks](https://shop.opentrons.com/collections/opentrons-tips) (for Purification)</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **P20-Multi Mount**: Specify which mount the [Opentrons P20 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette) is attached to.
* **P300-Multi Mount**: Specify which mount the [Opentrons P3000 8-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette) is attached to.
* **Labelling Step**: Specify whether or not to run the labelling portion.
* **Purification Step**: Specify whether or not to run the purification portion.





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
71381b
