# Twist Library Prep || Part 1: Fragmentation & Repair

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Twist Library Prep


## Description
This protocol is [part one](https://develop.protocols.opentrons.com/protocol/21e4d8-pt1) of a three-part series to automate the [Twist Library Prep protocol](https://www.twistbioscience.com/sites/default/files/resources/2019-09/Protocol_NGS_EnzymaticFragUniversalAdapterSystem_11Sep19_Rev1.pdf). See below for all three parts:</br>
</br>
Part 1: [Fragmentation & Repair](https://develop.protocols.opentrons.com/protocol/21e4d8-pt1)</br>
Part 2: [Ligate Adapters](https://develop.protocols.opentrons.com/protocol/21e4d8-pt2)</br>
Part 3: [PCR Amplification](https://develop.protocols.opentrons.com/protocol/21e4d8-pt3)</br>
</br>
This protocol begins with samples diluted to 5ng/µL (if you still need to normalize your sample concentration, try our [Normalization protocol](https://protocols.opentrons.com/protocol/normalization)) in either PCR tubes or a 96-well plate. Enzymatic Fragmentation Mastermix (40µL) is added to empty PCR tubes/96-well plate first, before 10µL of normalized sample is added. The PCR tubes/96-well plate containing sample and mastermix should then be moved off deck to thermocycler and run on the program listed in the [Twist Library Prep protocol](https://www.twistbioscience.com/sites/default/files/resources/2019-09/Protocol_NGS_EnzymaticFragUniversalAdapterSystem_11Sep19_Rev1.pdf). After the thermocycler, the samples can be returned to the OT-2 for [part two](https://develop.protocols.opentrons.com/protocol/21e4d8-pt2) of this protocol.</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 (Single- or Multi-Channel) Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons p300 (Single- or Multi-Channel) Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* *optional*: [Opentrons Thermocycler](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module) or [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck), for active cooling during protocol
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) or [Aluminum Block Set](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)
* [Microcentrifuge Tube, 1.5mL](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) or PCR strips
* Samples
* [Twist Enzymatic Fragmentation and Twist Universal Adapter System](https://www.twistbioscience.com/resources/protocol/enzymatic-fragmentation-and-twist-universal-adapter-system-use-twist-ngs)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 1: Normalized samples in [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) or PCR tubes on [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)</br>
</br>
Slot 2 (if using P300 Single-Channel): Enyzmatic Fragmentation Master Mix in [Microcentrifuge Tube, 1.5mL](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) in [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) or [24-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)</br>
*Tubes should be loaded in A1, A2, and A3; each tube can accommodate up to 32 samples and will be used sequentially*</br>
Slot 2 (if using P300 Multi-Channel): Enyzmatic Fragmentation Master Mix in [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) or PCR tubes on [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)</br>
*Columns 1, 2, and 3 should be loaded; each column can accommodate up to 32 samples and will be used sequentially*</br>
</br>
Slot 3: [Opentrons Tips for P300](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 6: [Opentrons Tips for P20](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 7: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) or PCR tubes on [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set) with optional [Opentrons Thermocycler](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module) or [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck), for active cooling during protocol</br>
</br>

**Using the customizations field (below), set up your protocol.**
* **P20 Type**: Select the type (Single- or Multi-Channel) to use; P20 should should be mounted on the left mount
* **P300 Type**: Select the type (Single- or Multi-Channel) to use; P300 should should be mounted on the right mount
* **Number of Samples**: Specify the number of samples to run (1-96).
* **Module (for cooling)**: Select whether or not an Opentrons module will be used for active cooling during protocol
* **Destination Plate**: Select the labware that will be used to combine the samples and the master mix
* **Sample Plate**: Select the labware that will contain the gDNA samples
* **Master Mix Labware**: Select the labware that will contain the enzymatic fragmentation master mix
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
21e4d8-pt1
