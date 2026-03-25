# Plate Aliquoting with CSV

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Aliquoting

## Description
This protocol aliquots a user-specified volume found in an uploaded CSV from a source column on a source plate, and then distributes to destination columns on 3 destination plates.

Another parameter that is controlled via the CSV is source column aspiration height above the bottom of the source wells.

Explanation of complex parameters below:
* `CSV`: Upload a CSV which specifies the following parameters -
the CSV should be formatted like so:

`Source Column` | `Source Aspiration Height from Bottom` | `Volume Aspirated`| `Volume Dispensed`

Example Row: `1`, `1`, `40`, `12`,

The first row should contain headers (like above). All following rows should just include necessary information. </br>

The `Volume Aspirated` will be dispensed from the source column to the analogous column in all 3 destination plates (e.g. 40 ul from column 1 will be aspirated, with 12ul being dispensed into column 1 of all 3 destination plates according to the example row above. )

* `Mount`: Specify which side the P300 Multi GEN2 pipette will be mounted.
* `Source Plate`: Specify which plate you will be using as the source plate on Slot 1 of the deck.  
* `Destination Plate 1 - Slot 4`: Specify which plate you will be using as the destination plate on Slot 4 of the deck.
* `Destination Plate 2 - Slot 7`: Specify which plate you will be using as the destination plate on Slot 7 of the deck.
* `Destination Plate 3 - Slot 10`: Specify which plate you will be using as the destination plate on Slot 10 of the deck.
* `Dispense Height`: Specify the height (in mm) above the bottom of the well for dispenses (e.g. a value of `1` is 1mm above the bottom of the well)
* `Aspirate Speed`: Specify the speed (in ul/sec) to aspirate liquid.
* `Dispense Speed`: Specify the speed (in ul/sec) to dispense liquid.

---

### Modules
No modules are required for this protocol.

### Labware
* [Bio-RAD 96 Well Plate 200ul PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*10feo1p*_gcl_aw*R0NMLjE2MTcwNjQ4OTguQ2owS0NRanc5WVdEQmhEeUFSSXNBRHQ2c0dhUUYzZ19ranNKV2R6Z1R6UmdzdG5QeE1DRmNBWm9zNEk3NFJ3YUpDUTItTWI2UDg4Xy1qWWFBbThnRUFMd193Y0I.*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYxOTIwMTM3Mi4xODcuMS4xNjE5MjAxNDIxLjA.&_ga=2.87335384.1162033746.1618926044-845401356.1612190477&_gac=1.122034937.1617064898.Cj0KCQjw9YWDBhDyARIsADt6sGaQF3g_kjsJWdzgTzRgstnPxMCFcAZos4I74RwaJCQ2-Mb6P88_-jYaAm8gEALw_wcB)
* [NEST 96 2mL Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?_gl=1*10feo1p*_gcl_aw*R0NMLjE2MTcwNjQ4OTguQ2owS0NRanc5WVdEQmhEeUFSSXNBRHQ2c0dhUUYzZ19ranNKV2R6Z1R6UmdzdG5QeE1DRmNBWm9zNEk3NFJ3YUpDUTItTWI2UDg4Xy1qWWFBbThnRUFMd193Y0I.*_ga*ODQ1NDAxMzU2LjE2MTIxOTA0Nzc.*_ga_GNSMNLW4RY*MTYxOTIwMTM3Mi4xODcuMS4xNjE5MjAxNDIxLjA.&_ga=2.87335384.1162033746.1618926044-845401356.1612190477&_gac=1.122034937.1617064898.Cj0KCQjw9YWDBhDyARIsADt6sGaQF3g_kjsJWdzgTzRgstnPxMCFcAZos4I74RwaJCQ2-Mb6P88_-jYaAm8gEALw_wcB)
* Thomas Sci LabForce 96 Well Plate 200ul
* FisherSci 96 Well Plate 1mL



### Pipettes
* [P300-Multi GEN 2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885m)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3d02be/Screen+Shot+2021-04-23+at+2.26.08+PM.png)

---

### Protocol Steps
1. Aspirate user-specified volume (from csv) from Column 1 of Source Plate (8-Channel p300)
2. Dispense user-specified volume (from csv) into Column 1 of Destination Plate A (8-Channel p300)
3. Dispense user-specified volume (from csv) into Column 1 of Destination Plate B (8-Channel p300)
4. Dispense user-specified volume (from csv) into Column 1 of Destination Plate C (8-Channel p300)
5. Discard Tips
6. Repeat steps 1-5 over the breadth of the CSV file.

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
3d02be
