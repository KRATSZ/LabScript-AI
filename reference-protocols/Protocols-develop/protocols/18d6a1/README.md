# MGI Easy Nucleic Acid Extraction Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Extraction


## Description
This protocol automates the [MGI Easy Nucleic Acid Extraction Kit](https://en.mgitech.cn/Uploads/Temp/file/20200416/5e97edc3ef00b.pdf) and offers the user the ability to modify parameters such as the number of samples and the types of labware used.</br>
</br>
This protocol has been optimized for use on the OT-2 and begins with an empty deepwell plate on the Magnetic Module. Lysis mix is first added to the plate, then samples are transferred to the lysis mix and mixed. Three wash steps occur after this and the protocol concludes with an elution step that results in 75µL of elutes transferred to a clean plate.
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* 96-Well Plate Containing Samples (such as the [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate))
* 96-Deepwell Plate for Extraction on the Magnetic Module (such as the [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate))
* 96-Well Plate for Elutes (such as the [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt))
* MGI Easy Nucleic Acid Extraction Kit



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
**Slot 1**: 96-Well Plate for Elutes (such as the [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt))
</br>
</br>
**Slot 2**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack 5
</br>
</br>
**Slot 3**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
A1: Lysis Mix (Samples 1-32)
</br>
A2: Lysis Mix (Samples 33-64)
</br>
A3: Lysis Mix (Samples 65-96)
</br>
A4: Wash Buffer 1 (Samples 1-48)
</br>
A5: Wash Buffer 1 (Samples 49-96)
</br>
A6: Wash Buffer 2 (Samples 1-48)
</br>
A7: Wash Buffer 2 (Samples 49-96)
</br>
A8: Wash Buffer 3 (Samples 1-48)
</br>
A9: Wash Buffer 3 (Samples 49-96)
</br>
A10: *Empty*
</br>
A11: *Empty*
</br>
A12: Nuclease-Free Water (Samples 1-96)
</br>
</br>
**Slot 4**: 96-Well Plate Containing Samples (such as the [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate))
</br>
</br>
**Slot 5**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack 3
</br>
</br>
**Slot 6**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack 4
</br>
</br>
**Slot 7**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack for Samples
</br>
</br>
**Slot 8**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack 1
</br>
</br>
**Slot 9**: [Opentrons Tip Racks for P300](https://shop.opentrons.com/collections/opentrons-tips) - Tip rack 2
</br>
</br>
**Slot 10**: [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with 96-Deepwell Plate for Extraction (such as the [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate))
</br>
</br>
**Slot 11**: [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) (liquid waste)
</br>
</br>
*Note about Tip Racks*: Each column of samples (8) will require five columns of tips + the tips needed for the initial sample transfer. 
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify the number of samples to run.
* **Sample Plate (input) Type**: Select the type of plate used.
* **Extraction Plate (MagPlate) Type**: Select the type of plate used.
* **Elution Plate (output) Type**: Select the type of plate used.
* **P300-Multi Mount**: Select which mount (left, right) the P300-Multi is attached to.
* **Tip Type**: Specify the type of tips (filtered, non-filtered) used.
* **Used Tips Destination**: Specify the destination of used tips. "Empty Tipracks" is best suited for runs of more than 24 samples.




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
18d6a1
