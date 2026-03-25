# PCR Clean-Up for Illumina 16S

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina 16S


## Description
This protocol automates the PCR Clean-Up step of the [Illumnia 16S kit](https://support.illumina.com/downloads/16s_metagenomic_sequencing_library_preparation.html) with a slight modification to volumes.</br>
</br>
Beginning with a starting volume of sample (input by user), 20µL of AMPure XP beads is added to each well. After incubation on the Magnetic Module, the supernatant is removed and two ethanol wash steps occur (with 195µL added to each well). Finally, 30µL of 10 mM Tris pH 8.5 or molecular grade water is added to each well and after incubation, 25µL of supernatant is transferred to a clean PCR plate.</br>
</br>
This protocol requires an Opentrons [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) and the [GEN2 P300 and P20 8-Channel Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette), in addition to the Illumina 16S kit and labware (more information below).
</br>
</br>
If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P300 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons P20 Multi-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tip Rack(s)](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* Samples
* Reagents (AMPure XP beads, 80% Ethanol, and 10 mM Tris pH 8.5 or molecular grade water)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

This protocol utilizes a variable number of 200µL filter tips, depending on the number of samples input (below). Each column of samples requires six (6) columns of tips. The protocol will use 200µL filter tipracks from slots in the following order: 8, 9, 5, 6, 2, and 3. Given this, if running 8 samples, only the first 6 columns of tips in slot 8 would be used. Additionally, tips used for adding ethanol are used again to remove supernatant. Finally, tips used after the addition of beads and removal of first supernatant, are replaced in empty slots/tipracks for easier disposal and to prevent waste bin from getting too full.</br>
</br>
**Deck Layout**</br>
</br>
Slot 1: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) (clean and empty for elutes)</br>
</br>
Slot 2: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 5)</br>
</br>
Slot 3: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 6)</br>
</br>
Slot 4: [Opentrons 20µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)</br>
</br>
Slot 5: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 3)</br>
</br>
Slot 6: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 4)</br>
</br>
Slot 7: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (for reagents)</br>
A1: AMPure XP beads (20µL per sample)</br>
A2: 80% Ethanol, wash 1, samples 1-48 (195µL per sample)</br>
A3: 80% Ethanol, wash 1, samples 49-96 (195µL per sample)</br>
A4: 80% Ethanol, wash 2, samples 1-48 (195µL per sample)</br>
A5: 80% Ethanol, wash 2, samples 49-96 (195µL per sample)</br>
A6: 10 mM Tris pH 8.5 or molecular grade water (30µL per sample)</br>
</br>
Slot 8: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 1)</br>
</br>
Slot 9: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (Rack 2)</br>
</br>
Slot 10: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing samples</br>
</br>
Slot 11: [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) (for liquid waste)</br>
</br>


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol.
2. Upload [custom labware definition](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols), if needed.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
14b685
