# PCR Prep and Pooling with 384 Plates - Stage 2


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep

## Description
This protocol is Stage 2 of a 3 part PCR Prep protocol. Parts 1 and 3 can be found below. For detailed protocol details, please reference the "Protocol Steps" section.

[Stage 1 Protocol](https://protocols.opentrons.com/protocol/08fd01)
[Stage 3 Protocol](https://protocols.opentrons.com/protocol/08fd01-pt3)

---

### Labware
* Nest 12 Well Reservoir
* Opentrons 20ul Filter tips
* Custom 384 well plate
* 96 Index Plate

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/08fd01/Screen+Shot+2022-09-12+at+7.12.19+AM.png)


---

### Protocol Steps
1. Transfer 16 uL of Master mix from reservoir trough to all wells in 384 well plate (same tips) in
position 8 (PCR 2 Plate). Use tip box in position 3 discard the tips into the waste.
2. Use multidispense 2uL times 4 (take up 8uL and dispense 2 4 times in order to maximize
efficiency) of INDEX from plate in position 7 (INDEX) (a1) to plate in position 8 (PCR 2 plate)
(a1,b1,a2,b2). A2 to (a2,b2,a4,b4) etc (see provided picture for explanation) discard the tips to their
original box after each step.
3. Transfer 2uL of sample from plate in position 9 (PCR 2 pooled plate) to plate in position 8 (PCR 2
plate). A1 to A1, A2 to A2 etc… see picture attached. Discard the tips into their original box location
after every transfer.

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
08fd01-pt2
