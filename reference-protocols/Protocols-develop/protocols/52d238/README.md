# NEB Ultra II FS DNA Library Prep (Part 2)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* NEB Ultra II FS DNA Library Prep


## Description
This protocol automates the PCR, Bead Clean Up and Elution steps of the [NEB Ultra II FS DNA Library Prep](https://www.neb.com/products/e7805-nebnext-ultra-ii-fs-dna-library-prep-kit-for-illumina#Protocols,%20Manuals%20&%20Usage)


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P20-multi channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300-multi channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons Thermocycler Module](https://opentrons.com/modules/thermocycler-module/)
* [Opentrons Temperature Module](https://opentrons.com/modules/temperature-module/)
* [Opentrons Magnetic Module](https://opentrons.com/modules/temperature-module/)
* [NEST 100uL PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 96 Well Aluminum Block with 200 uL PCR Strips](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

* Thermocycler (Slot 7)
* Temperature Module (Slot 4)
* Magnetic Module (Slot 9)
* Plate with Index-Primers (Slot 5)
* Opentrons 200 uL Filter Tips (Slot 2, 3)
* Opentrons 20 uL Filter Tips (Slots 1)

Initial Starting State:
- Samples with beads in a 96 well PCR plate in the thermocycler.
- EB Tween is in column 1 on the 96 Well Aluminum block on the temperature module.
- Reservoir channel A1 contains ethanol
- Plate on the magnetic module contains pre-aliquoted magnetic beads
- Plate with Index-Primers starts in a 96 well plate on Position 5 of deck



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples, the mounts for each pipette, and whether to run each part of the protocol.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
52d238