# PCR/qPCR Prep

### Author
[Opentrons](https://opentrons.com/)


## Categories
* PCR
	* PCR Prep
## Description
This is a specific protocol for aliquoting liquid from three reagent plates to three 96 deep well plates using a multi-channel p300 pipette. Tips are changed between reagents. Either pipette mount can be specified in setup.
* 350ul SPR Wash Buffer is added to a 96 deep well plate
* 350ul VHB Buffer is added to a second 96 deep well plate
* 50ul nuclease free water is added to a third 96 deep well plate

* 'P300-Multi Mount Side': Left or right refers to the pipette mount side

### Labware
* [3x NEST 1 Well Reservoir 195ml](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [3x NEST 96 Deepwell Plate 2ml](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)

### Pipettes
* [P300 Multi-Channel Gen2](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* SPR Wash Buffer
* VHB Buffer
* Nuclease Free Water

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3308b4/Screen+Shot+2022-03-27+at+8.43.58+PM.png)

### Reagent Setup
* SPR Wash Buffer in NEST 1 Well Reservoir 195ml: slot 4

	Minimum fill: 34ml
* VHB Buffer in NEST 1 Well Reservoir 195ml: slot 5

	Minimum fill: 34ml
* Nuclease Free Water in NEST 1 Well Reservoir 195ml: slot 6

	Minimum fill: 5ml

---

### Protocol Steps
1. A fresh tip is picked up.
2. 350ul of SPR Wash Buffer is transferred from slot 4 to individual wells on the 96 deepwell plate in slot 7 in two movements of 175ul. Using the 8-channel pipette, the transfer occurs from column 1 to column 11
3. Tips are deposited in the trash (slot 12)
4. A fresh tip is picked up.
5. 350ul of VHB Buffer is transferred from slot 5 to individual wells on the 96 deepwell plate in slot 8 in two movements of 175ul. Using the 8-channel pipette, the transfer occurs from column 1 to column 11
6. Tips are deposited in the trash (slot 12)
7. A fresh tip is picked up.
8. 50ul of Nuclease Free Water is transferred from slot 6 to individual wells on the 96 deepwell plate in slot 9 in a single movement. Using the 8-channel pipette, the transfer occurs from column 1 to column 11
9. Tips are deposited in the trash (slot 12)

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
3308b4
