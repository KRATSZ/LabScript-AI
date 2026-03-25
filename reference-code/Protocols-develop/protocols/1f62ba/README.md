# PCR Prep with Strip Tubes

### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep

## Description
This protocol preps one PCR plate with DNA, water, primer letter, primer number, and Kappa enzyme. New tips are granted for DNA and primers, whereas just one column of tips is used for the Kappa enzyme and water, respectively. The water is added via multi-dispensing.


Explanation of complex parameters below:
* `Number of Columns`: Specify the number of DNA columns for this protocol.
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 multi-channel pipette.

---

### Labware
* [Nest 12-well reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [20ul Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


---

### Deck Setup
![deck layout]()


---

### Protocol Steps
1. Add 3ul of Water to each PCR well
2. Add 10ul of Kapa Enzyme to each PCR well
3. Add 1ul of Primer Number to each PCR well
4. Add 1ul of Primer Letter to each PCR well
5. add 5ul of DNA to each PCR well

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
1f62ba
