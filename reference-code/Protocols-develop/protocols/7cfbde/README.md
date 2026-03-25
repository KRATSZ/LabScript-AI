# 3D Black Bio RNA Extraction

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction


## Description
This protocol automates RNA extraction according to the 3D Black Bio RNA Extraction Kit.</br>
</br>
Using the P300 Multi-Channel Pipette, this protocol can accommodate up to 96 samples per run and can be configured to run any multiple of 8 up to 96. Starting with at least 200µL of sample in a standard 96-well plate, the entire process is automated and ends with 60µL of elution containing RNA dispensed into a 96-well PCR plate. The elution is then ready for RT/qPCR, Next-Gen Sequencing, hybridization, etc.</br>
</br>

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) (recommended) or [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [NEST 96-Deep Well Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* PCR Tubes
* 3D Black Bio Extraction Kit
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Reagent Preparation**</br>
Prepare all reagents according to manual.</br>
</br>
**Proteinase K**: At least 10µL (12µL is recommended) per column of samples should fill a PCR Strip.</br>
The PCR strip should be placed in column 1 of the [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)</br>
</br>
**MagBeads**: At least 20µL (22µL is recommended) per column of samples should fill 1 (or 2, if processing more than 48 samples) PCR strip(s).</br>
The PCR strip(s) should be placed in column(s) 3 (and 4, if processing more than 48 samples) of the [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)</br>
</br>
**Lysis-Binding Mix**: In slots 1-6 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml).</br>
For every column (8 samples), 7mL of Lysis-Binding Mix should be added to the reservoir. Each slot of the 12 well reservoir can accommodate volume for 2 columns/16 samples and should be loaded sequentially (ex. if running 24 samples, slot 1 would get 14mL lysis-binding mix, slot 2 would get 7mL lysis-binding mix, slot 3 would be empty, etc).</br>
</br>
**Wash 1**: In slots 7-12 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml).</br>
For every column (8 samples), 6.5mL of wash 1 should be added to the reservoir. Each slot of the 12 well reservoir can accommodate volume for 2 columns/16 samples and should be loaded sequentially (ex. if running 24 samples, slot 7 would get 13mL wash 1, slot 8 would get 6.5mL wash 1, slot 9 would be empty, etc).</br>
</br>
**Wash 2**: In [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml).</br>
For every column (8 samples), 14mL of wash 2 should be added to the reservoir.</br>
</br>
**Elution Buffer**: At least 60µL (65µL is recommended) per column of samples should fill a PCR Strip. Each PCR strip can accommodate up to two columns worth (16) samples.</br>
The PCR strips should be loaded in columns 7-12 of the [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
</br>
</br>
**Deck Layout**</br>
</br>
**Slot 1:** [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt), containing samples</br>
**Slot 2:** [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) containing **Wash 2**</br>
**Slot 3:** [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 4:** [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) containing **Proteinase K**, **Magnetic Beads**, and **Elution Buffer**</br>
**Slot 5:** [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) containing **Lysis-Binding Mix** and **Wash 1**</br>
**Slot 6:** [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 7:** [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Deep Well Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)</br>
**Slot 8:** [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 9:** [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 10:** [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml), empty for liquid waste</br>
**Slot 11:** [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml), empty for liquid waste</br>
</br>
*Note about tips*: The tips in slot 8 will be used for removing supernatant and used tips will be returned to empty tip racks to prevent overflow of the waste bin.</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **P300-Multi Mount**: Select which mount the P300-Multi is attached to
* **Number of Samples**: Specify the number of samples to run



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7cfbde
