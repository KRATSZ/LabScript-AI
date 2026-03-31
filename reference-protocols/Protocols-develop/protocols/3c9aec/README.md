# Cell Culture Prep with CSV Input

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sterile Workflows
	* Cell Culture

## Description
This protocol preps a 96 well plate with cell culture and a variety of reagents. First, the protocol parses the csv to check for wells which have a confluency value of greater than 85. These values will be referenced and added to for the duration of the protocol. If there are a group of confluency wells with a value of greater than 85 in a single column, the multi-channel pipette will be used, only picking up the number of tips necessary. The user may be asked to replace tips if the protocol runs out. Note that a volume of at least 3mL of any reagent should be in each reservoir well AFTER the protocol is completed (i.e. there should never be > 3mL of reagent at any point of the protocol). See protocol steps below for details.

Explanation of complex parameters below:
* `csv file`: Upload the csv file as so:
```
Well,Confluency
A1, 90
B1, 83
```
* `Temperature module temperature (C)`: Specify temperature module temperatre in celsius
* `First step aspiration rate (moving to waste)`: Specify the aspiration rate in step 1 of the protocol when included wells are moved to waste, where 1.0 is default, 1.5 is 50% faster, and 0.2 is 20% default speed, for example.
* `PBS Dispense Flow Rate`: The PBS will be dispesed into the plate 2mm from the side of the well to avoid separation of culture. Specify the flow rate, where 1.0 is default, 1.5 is 50% faster, and 0.2 is 20% default speed, for example.
* `Incubation Time (minutes)`: Specify the incubation time i nminutes after trypsin is added to the plate.
* `Media Aspirate X (ul)`: Specify volume of media to move from column 12 of the reservoir to the plate.
* `Media Dispense Y (ul)`: Specify the volume of the second media to be added to the plate.
* `Track tips?`: Yes for tracking tips, no for fresh tip boxes.
*  `P300 Single-Channel Mount`: Specify which mount (left or right) to host your P300 pipettes.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Corning 360ul 96 well plate flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [NEST 12 well Reseroir 195mL](https://shop.opentrons.com/verified-labware/well-reservoirs/)
* [Opentrons 200ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/)


### Pipettes
* [Opentrons P300 Single-Channel Pipette GEN2](https://shop.opentrons.com/pipettes/)
* [Opentrons P300 Multi-Channel Pipette GEN2](https://shop.opentrons.com/pipettes/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3c9aec/Screen+Shot+2022-01-20+at+10.56.28+AM.png)


---

### Protocol Steps
1. Move 200ul of included wells (confluency greater than 85) to waste
2. 150ul pbs to included wells
3. Removing PBS from plate (175ul)
4. Transfer 25ul of trypsin to included wells
5. Move media to plate (140ul)
6. Aspirate media to waste
7. Dispense second media to plate.

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
3c9ec
