# Nucleic Acid Extraction

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Extraction


## Description
This protocol automates a nucleic acid extraction using the [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) and incorporates the Axygen 300µL plate (holding samples and elutes).</br>
</br>
This protocol begins with 20µL of sample in the Axygen plate and 20µL of magnetic beads are added and mixed. After removing the supernatant, there are two subsequent washes with ethanol (150µL per sample). Finally, 50µL of elution buffer is added to the sample wells and after incubation, the elution is transferred to a second Axygen plate.</br>
</br>
Between 1 and 96 samples can be processed with this protocol using the [GEN2 p300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette). Because the 8-channel pipette is used, the protocol will behave as if a multiple of eight is used (ex. if you select 10 samples, the protocol will behave in the same way as if you selected 16 samples) - please plan reagent consumption accordingly.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons p300 Multi-Channel Pipette, GEN2](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* Axygen 300µL Plate
* Reagents (magnetic beads, ethanol, elution buffer)
* Samples



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

The [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) should be placed in **slot 6** with an Axygen plate containing samples on top.</br>
</br>
The [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) should be placed in **slot 5** with the following reagnets:
* Magnetic Beads: **Slot 8**
* Ethanol (for wash 1): **slot 6** (for samples 1-48), **slot 5** (for 48+ samples)
* Ethanol (for wash 2): **slot 4** (for samples 1-48), **slot 3** (for 48+ samples)
* Elution Buffer: **slot 1**

</br>
</br>
The [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) should be placed in **slot 9** for liquid waste.</br>
</br>
An empty Axygen plate should be placed **in slot 3**, for elutes.</br>
</br>
The [Opentrons Tiprack(s)](https://shop.opentrons.com/collections/opentrons-tips) will be accessed in the following order: **slot 1**, **slot 2**, **slot 4**, **slot 7**, **slot 10**, **slot 11**. Each tiprack contains 12 columns of tips and this protocol will use 6 columns of tips per column of sample.
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **p300 Multi Mount**: Select which mount (left, right) the p300 Multi is attached to.
* **Number of Samples**: Specify the number of samples to run (1-96).
</br>
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
245eb2
