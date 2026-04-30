# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This is a PCR Prep protocol. The protocol begins by adding mastermix to the PCR plate and then adds in the samples. The user has prompted to pause at various points.

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Opentrons 300uL Tips](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/)
* [Opentrons 20µL Tips](https://shop.opentrons.com/opentrons-20-l-tips-160-racks-800-refills/)

### Pipettes
* [P300, 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20, 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Protocol Steps
1. Transfer 23uL of master mix using the 200uL multichannel pipette from the reservoir on the temp module to wells A1-A12 on the PCR Plate in slot 3.
2. Transfer 2uL of sample using the 20uL multichannel pipette from the sample PCR plate in slot 5 to the master mix PCR plate in slot 3 and mix twice.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0fdc01
