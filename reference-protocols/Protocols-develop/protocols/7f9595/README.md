# Sample Serial Dilution (1:10)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Serial Dilution

## Description
This protocol automates the serial dilution of two separate sample columns and also adds PBS buffer to the necessary wells. It will perform additional mixing steps before and after the addition of reagents. Each transfer performs a blow out in the destination well.

Serial Dilution Plate Map:
![Serial Dilution Plate Map](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7f9595/7f9595_dilution_map.png)

Explanation of parameters below:
* `P300 Multichannel GEN2 Mount`: Specify which mount (left or right) to load the P300 multi channel pipette.
* `Reservoir Type`: Specify the type of reservoir being used in Slot 1.
* `Blowout Height from Well Bottom (mm)`: The height the blowout should occur from the bottom of the well. For example, a volume of 200 uL in this plate will have a height of approximately 5.4 mm from the bottom of the well.
* `Mix Aspiration Flow Rate (uL/s)`: Flow rate when aspiration occurs in a mixing step.
* `Mix Dispensing Flow Rate (uL/s)`: Flow rate when dispensing occurs in a mixing step.

---

### Labware
* [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

### Pipettes
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7f9595/7f9595.png)

---

### Protocol Steps

1. PBS buffer starts in row 1 of 12 row trough; chemical mix of 200 uL starts in column 1 and column 7 of 96-well Costar microplate (both labwares are Opentron verified)
2. Add 180uL of PBS buffer from trough to column 2, 3,4,5,6, 8, 9, 10, 11, 12. Change tips.
3. Mix column 1 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 1 to column 2, mix 10 times at volume of 20uL. Blowout. Change tips.
4. Mix column 7 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 7 to column 8, mix 10 times at mix volume of 20uL. Blowout.Change tips.
5. Mix column 2 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 2 to column 3, mix 10 times at mix volume of 20uL. Blowout.Change tips.
6. Mix column 8 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 8 to column 9, mix 10 times at mix volume of 20uL. Blowout.Change tips
7. Mix column 3 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 3 to column 4, mix 10 times at mix volume of 20uL. Blowout.Change tips.
8. Mix column 9 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 9 to column 10, mix 10 times at mix volume of 20uL. Blowout. Change tips
9. Mix column 4 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 4 to column 5, mix 10 times at mix volume of 20uL. Blowout.Change tips.
10. Mix column 10 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 10 to column 11, mix 10 times at mix volume of 20uL. Blowout.Change tips
11. Mix column 5 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 5 to column 6, mix 10 times at mix volume of 20uL. Blowout. Change tips.
12. Mix column 11 using P300-8-channel 6 times with 200 uL volume and add 20uL of chemical mix from column 11 to column 12, mix 10 times at mix volume of 20uL. Blowout. Change tips

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
7f9595