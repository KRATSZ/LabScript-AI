# PCR Prep and Pooling with 384 Plates - Stage 3


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep

## Description
This protocol is Stage 3 of a 3 part PCR Prep protocol. Parts 1 and 2 can be found below. For detailed protocol details, please reference the "Protocol Steps" section.

[Stage 1 Protocol](https://protocols.opentrons.com/protocol/08fd01)
[Stage 2 Protocol](https://protocols.opentrons.com/protocol/08fd01-pt2)

---

### Labware
* Opentrons 20ul Filter tips
* Custom 384 well plate(link to labware on shop.opentrons.com when applicable)
* Nest 96 Wellplate 100ul PCR Full Skirt

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/08fd01/Screen+Shot+2022-09-12+at+7.12.44+AM.png)


---

### Protocol Steps
1. Transfer 3 uL of sample from plate in position 8 (PCR 2 Plate). Columns A1, A3, A5,A7, etc.. to
Plate in position 5 column A1 (1 96 well plate equivalent into the same column). For pipetting do 3
aspirations per transfer in the following fashion 3uL A1 3ul air gap, 3uL A3 3ul air gap, 3uL A5 transfer to
A1 in the destination plate with a blowout at the end. Repeat until that set is done and discard the tips.
2. Transfer 3 uL of sample from plate in position 8 (PCR 2 Plate). Columns A2, A4, A6,A8, etc.. to
Plate in position 5 column A3 (1 96 well plate equivalent into the same column). For pipetting do 3
aspirations per transfer in the following fashion 3uL A2 3ul air gap, 3uL A4 3ul air gap, 3uL A6 transfer to
A3 in the destination plate with a blowout at the end. Repeat until that set is done and discard the tips.
3. Transfer 3 uL of sample from plate in position 8 (PCR 2 Plate). Columns B1, B3, B5,B7, etc.. to
Plate in position 5 column A5 (1 96 well plate equivalent into the same column). For pipetting do 3
aspirations per transfer in the following fashion 3uL B1 3ul air gap, 3uL B3 3ul air gap, 3uL B5 transfer to
A5 in the destination plate with a blowout at the end. Repeat until that set is done and discard the tips.
4. Transfer 3 uL of sample from plate in position 8 (PCR 2 Plate). Columns b2, b4, b6,b8, etc.. to
Plate in position 5 column A7 (1 96 well plate equivalent into the same column). For pipetting do 3
aspirations per transfer in the following fashion 3uL b2 3ul air gap, 3uL b4 3ul air gap, 3uL b6 transfer to
A7 in the destination plate with a blowout at the end. Repeat until that set is done and discard the tips.

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
08fd01-pt3
