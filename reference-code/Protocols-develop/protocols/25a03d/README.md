# qPCR Prep in Triplicates

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* PCR
	* PCR Prep

## Description
This protocol preps a 96-well plate with mastermix and DNA with one column for controls. The mastermix is viscous and handled accordingly with air gaps, touch tips, blow outs, delays after aspiration, as well as a decreased pipetting flow rate. Mastermix is added into every third column dependent on how many samples are selected, and the control column is added afterwards. After DNA is added to the mastermix and mixed, 20ul of the solution are transferred to the two subsequent columns following that column of interest.

Explanation of complex parameters below:
* `Number of Samples (not including controls, 1-24)`: Specify the number of samples not including controls for this run.
* `Final Plate Labware Type`: Specify which piece of labware will be used as the final sample plate for this protocol.
* `Control Plate Labware Type`: Specify which piece of labware will be used to hold the control.
* `Aspiration/Dispense Flow rates`: Specify the global aspiration/dispense flow rates for the P300 and P20 pipettes. A value of 1.0 is default, a value of 0.5 is 50% of the default flow rate, 1.2 a 20% increase in default flow rate, etc. 
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 multi-channel pipette.
* `P300 Single-Channel Mount`: Specify which mount (left or right) to host the P300 single-channel pipette.

---

### Labware
* [Opentrons 96 well aluminum block with tube strips](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* [Opentrons 24 well aluminum block](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* Custom tip racks
* Custom 96 well plate

### Pipettes
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/25a03d/Screen+Shot+2021-09-30+at+12.26.42+PM.png)


---

### Protocol Steps
1. Use p300 single channel pipette to transfer 48ul of MasterMix (MM) from 2.0 ml tube (slot 1) to columns 1, 4, 7, and 10 of the plate/strip tubes in slot 4 (final qPCR plate). Want to be able to use either strip tubes or a plate for the final qPCR reactions in slot 4. Solution will be viscous so want to make sure all is expelled from tips.
2. Use p20 multi-channel pipette to transfer 12ul of DNA from strip tubes in slot 7 to the final qPCR plate in slot 4. Transfer column 1 of DNA samples to column 1 of final plate; column 2 of DNA samples to column 4 of final plate; and column 3 of DNA samples to column 7 of final plate.
3. Use p20 multi-channel pipette to transfer 12ul of DNA from strip tubes in slot 9 to the final qPCR plate in slot 4. Transfer column 12 of strip tubes to column 10 of plate. (Could possibly put this strip tube with the DNA in slot 7 but would want it to remain in column 12 so it is not near the other DNA samples. This is the control DNA and we do not want to contaminate the test samples).
4. Use p20 multi-channel pipette to mix column 1 of final qPCR plate (slot 4) 5 times (set a 20ul). Then transfer 20ul of column 1 to column 2 and column 3 of the final qPCR plate. Repeat with MM/DNA sample in column 4 and transfer 20ul to columns 5 and 6. Repeat with MM/DNA sample in column 7 and transfer 20ul to columns 8 and 9. Repeat with MM/DNA sample in column 10 and transfer 20ul to columns 11 and 12. Solution will be viscous so want to make sure all is expelled from tips.



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
25a03d
