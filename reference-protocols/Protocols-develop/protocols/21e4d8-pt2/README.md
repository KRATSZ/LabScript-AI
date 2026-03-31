# Twist Library Prep || Part 2: Ligate Adapters

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Twist Library Prep


## Description
This protocol is [part two](https://develop.protocols.opentrons.com/protocol/21e4d8-pt2) of a three-part series to automate the [Twist Library Prep protocol](https://www.twistbioscience.com/sites/default/files/resources/2019-09/Protocol_NGS_EnzymaticFragUniversalAdapterSystem_11Sep19_Rev1.pdf). See below for all three parts:</br>
</br>
Part 1: [Fragmentation & Repair](https://develop.protocols.opentrons.com/protocol/21e4d8-pt1)</br>
Part 2: [Ligate Adapters](https://develop.protocols.opentrons.com/protocol/21e4d8-pt2)</br>
Part 3: [PCR Amplification](https://develop.protocols.opentrons.com/protocol/21e4d8-pt3)</br>
</br>
The final plate from [part one](https://develop.protocols.opentrons.com/protocol/21e4d8-pt1) should be run through the thermocycler program outlined in the [Twist Library Prep protocol](https://www.twistbioscience.com/sites/default/files/resources/2019-09/Protocol_NGS_EnzymaticFragUniversalAdapterSystem_11Sep19_Rev1.pdf) before being moved back to the OT-2 for this protocol.</br>
</br>
This protocol begins by adding 5µL of the Twist Universal Adapters to each well containing samples from [part one](https://develop.protocols.opentrons.com/protocol/21e4d8-pt1), followed by the addition of 45µL of Ligation Master Mix. The user is then prompted to remove plate and incubate the samples on a thermocycler. Following incubation, the user will return the plate to the OT-2 for a fully-automated magbead-based wash process (2 times) that will result in the 15µL of supernatant transferred to labware selected by the user. The user should then take the labware containing the supernatant and run on the thermocycler before moving to [part three](https://develop.protocols.opentrons.com/protocol/21e4d8-pt3).</br>
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
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* *Optional*, [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck), for active cooling during protocol
* Multi-Well Reservoir, such as the [NEST 12-Well Reservoir](https://labware.opentrons.com/nest_12_reservoir_15ml/) or [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml/)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) or [Aluminum Block Set](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)
* [Microcentrifuge Tube, 1.5mL](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) or PCR strips
* Samples
* [Twist Enzymatic Fragmentation and Twist Universal Adapter System](https://www.twistbioscience.com/resources/protocol/enzymatic-fragmentation-and-twist-universal-adapter-system-use-twist-ngs)
* *Optional*, Single-Well Reservoir, such as the [NEST 1-Well Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir) or [Agilent 1-Well Reservoir, 290mL](https://labware.opentrons.com/agilent_1_reservoir_290ml?category=reservoir), for liquid waste



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 1: Empty Destination PCR Labware (such as [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) or PCR Strips in [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set))</br>
</br>
Slot 2: Plate containing Twist Universal Adapters</br>
</br>
Slot 3: [Opentrons Tips for P300](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 4: Multi-Well Reservoir</br>
*Layout for 12-well reservoir:*</br>
A1: DNA Purification Beads (80µL per sample)</br>
A3: Freshly prepared 80% ethanol for wash 1, samples 1-48 (200µL per sample)</br>
A4: Freshly prepared 80% ethanol for wash 1, samples 48-96 (200µL per sample)</br>
A5: Freshly prepared 80% ethanol for wash 2, samples 1-48 (200µL per sample)</br>
A6: Freshly prepared 80% ethanol for wash 2, samples 48-96 (200µL per sample)</br>
A12: Elution solution (water, 10mM Tris-HCl pH, or Buffer EB) (17µL per sample)</br>
*Layout for 4-well reservoir:*</br>
A1: DNA Purification Beads (80µL per sample)</br>
A2: Freshly prepared 80% ethanol for wash 1, samples 1-96 (200µL per sample)</br>
A3: Freshly prepared 80% ethanol for wash 2, samples 1-96 (200µL per sample)</br>
A4: Elution solution (water, 10mM Tris-HCl pH, or Buffer EB) (17µL per sample)</br>
</br>
Slot 5: [Opentrons Tips for P20](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 6: [Opentrons Tips for P300](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 7: Labware containing ligation master mix (on [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck), if active cooling during protocol)</br>
</br>
Slot 10: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with plate from part one</br>
</br>
*Optional*, Slot 11: Single-Well Reservoir for liquid waste</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **P20 Type**: Select the type (Single- or Multi-Channel) to use; P20 should should be mounted on the left mount
* **P300 Type**: Select the type (Single- or Multi-Channel) to use; P300 should should be mounted on the right mount
* **Number of Samples**: Specify the number of samples to run (1-96)
* **Type of MagDeck**: Select which generation (1, 2) magnetic module to use
* **Plate on MagDeck**: Select which labware type contains samples and is placed on magnetic module
* **Module (for cooling)**: Select whether or not an Opentrons module will be used for active cooling during protocol
* **Destination Plate**: Select the labware that will be used for the elutions
* **Reservor for Reagents**: Select which reservoir will be used for reagents
* **Sample Plate**: Select the labware that will contain the gDNA samples
* **Master Mix Labware**: Select the labware that will contain the ligation master mix
* **Liquid Waste Destination**: Select where liquid waste should be disposed of
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
21e4d8-pt2
